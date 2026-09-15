#!/usr/bin/env python3
"""Check historical split isolation and tokenizer compatibility on a rebuilt corpus."""
import argparse
import json
from collections import Counter
from pathlib import Path

from transformers import AutoTokenizer

from triage_poc.comparison import sha256
from triage_poc.sft_termination import render_training_text
from triage_poc.source_sft_preflight import validate_source_sft_artifacts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("previous-canonical", "manifest", "artifacts", "original-tokenizer",
                 "candidate-tokenizer", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    previous_hash = sha256(args.previous_canonical)
    if previous_hash != "da7b7913cc70a4cd1c340d8afb1bfcc910af5eb7b8511f81b18f356d8420b347":
        raise ValueError("Expected the frozen v1 canonical artifact")
    previous = {r["record_id"]: r for r in map(json.loads,
                 args.previous_canonical.read_text().splitlines())}
    manifest, canonical, train, validation = validate_source_sft_artifacts(
        args.manifest, args.artifacts)
    current = {r["record_id"]: r for r in canonical}
    common = previous.keys() & current.keys()
    migrations = sum(previous[key]["split"] != current[key]["split"] for key in common)
    if migrations:
        raise ValueError("Historical split assignments changed")
    if any(r["transformation"]["content_truncated"] for r in canonical):
        raise ValueError("Rebuilt corpus still contains truncated records")
    original = AutoTokenizer.from_pretrained(str(args.original_tokenizer), local_files_only=True)
    candidate = AutoTokenizer.from_pretrained(str(args.candidate_tokenizer), local_files_only=True)
    if original.get_vocab() != candidate.get_vocab():
        raise ValueError("Candidate vocabulary differs from the archive")
    for row in train + validation:
        prompt_args = dict(tokenize=True, add_generation_prompt=True, enable_thinking=False)
        if original.apply_chat_template(row["messages"][:-1], **prompt_args) != (
            candidate.apply_chat_template(row["messages"][:-1], **prompt_args)
        ):
            raise ValueError("Candidate changed a generation prompt")
        expected = render_training_text(original, row, True)
        actual = candidate.apply_chat_template(row["messages"], tokenize=False,
                                               add_generation_prompt=False)
        if expected != actual:
            raise ValueError("Candidate changes more than the final response terminator")
    report = {"status": "passed_data_revision_checks", "previous_sha256": previous_hash,
        "dataset_sha256": manifest["artifacts"]["canonical"]["sha256"],
        "records": len(current), "split_counts": dict(Counter(r["split"] for r in canonical)),
        "retained_record_ids": len(common), "new_record_ids": len(current.keys() - previous.keys()),
        "removed_record_ids": len(previous.keys() - current.keys()),
        "historical_split_migrations": migrations, "truncated_records": 0,
        "development_prompts_checked": len(train) + len(validation), "changed_prompts": 0,
        "training_changes": "only_final_assistant_terminator",
        "vocabulary_unchanged": True, "test_rendered_count": 0,
        "code_sha256": sha256(Path(__file__)),
        "limits": ["No training, model reload, inference or clinical evaluation performed."]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
