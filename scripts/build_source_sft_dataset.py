#!/usr/bin/env python3
"""Build the 5,000-record source-derived bilingual medical QA SFT dataset."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from jsonschema import Draft202012Validator

from triage_poc.anonymization import TextAnonymizer
from triage_poc.sft_authoring_queue import (
    iter_frenchmedmcqa_anchors,
    iter_mediqal_anchors,
    iter_medquad_anchors,
    normalize_for_deduplication,
)
from triage_poc.source_sft import (
    SOURCE_DIRECT_IDENTIFIER_ENTITIES,
    build_source_sft_dataset,
    render_source_sft_conversation,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--medquad-repository", required=True, type=Path)
    parser.add_argument("--mediqal-repository", required=True, type=Path)
    parser.add_argument("--frenchmedmcqa-rebuilt", required=True, type=Path)
    parser.add_argument("--schema", required=True, type=Path)
    parser.add_argument("--output-directory", required=True, type=Path)
    parser.add_argument("--manifest-output", required=True, type=Path)
    parser.add_argument("--code-revision", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--previous-canonical", required=True, type=Path)
    return parser.parse_args()


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> dict[str, object]:
    content = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
    path.write_text(content, encoding="utf-8")
    return {
        "path": path.name,
        "record_count": len(rows),
        "byte_size": len(content.encode()),
        "sha256": hashlib.sha256(content.encode()).hexdigest(),
    }


def main() -> int:
    args = parse_args()
    if args.output_directory.exists() or args.manifest_output.exists():
        raise ValueError("Choose fresh versioned outputs; existing datasets must be preserved")
    prior_hash = hashlib.sha256(args.previous_canonical.read_bytes()).hexdigest()
    if prior_hash != "da7b7913cc70a4cd1c340d8afb1bfcc910af5eb7b8511f81b18f356d8420b347":
        raise ValueError("This v2 rebuild requires the frozen v1 canonical split assignments")
    previous = [json.loads(line) for line in args.previous_canonical.read_text().splitlines()]
    previous_splits = {row["record_id"]: row["split"] for row in previous}
    if len(previous_splits) != len(previous):
        raise ValueError("Previous canonical IDs are not unique")
    schema = json.loads(args.schema.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)

    mediqa_train = (
        anchor
        for anchor in iter_mediqal_anchors(args.mediqal_repository, include_options=True)
        if "/train.json:" in anchor.source_locator
    )
    french_train = (
        anchor
        for anchor in iter_frenchmedmcqa_anchors(args.frenchmedmcqa_rebuilt, include_options=True)
        if anchor.source_locator.startswith("train:")
    )
    records, summary = build_source_sft_dataset(
        {
            "medquad": iter_medquad_anchors(args.medquad_repository),
            "mediqal": mediqa_train,
            "frenchmedmcqa": french_train,
        },
        TextAnonymizer(entities=SOURCE_DIRECT_IDENTIFIER_ENTITIES),
        code_revision=args.code_revision,
        run_id=args.run_id,
        previous_splits=previous_splits,
    )
    for record in records:
        validator.validate(record)

    normalized_questions = [
        normalize_for_deduplication(record["instruction"]) for record in records
    ]
    if len(set(normalized_questions)) != len(records):
        raise ValueError("Post-anonymization question duplicates detected.")

    args.output_directory.mkdir(parents=True, exist_ok=True)
    canonical = _write_jsonl(args.output_directory / "source-sft-v2.jsonl", records)
    train_records = [record for record in records if record["split"] == "train"]
    validation_records = [record for record in records if record["split"] == "validation"]
    train = _write_jsonl(
        args.output_directory / "train-qwen3.jsonl",
        [render_source_sft_conversation(record) for record in train_records],
    )
    validation = _write_jsonl(
        args.output_directory / "validation-qwen3.jsonl",
        [render_source_sft_conversation(record) for record in validation_records],
    )
    manifest = {
        "schema_version": "1.0.0",
        "manifest_id": "derived-source-medical-qa-sft-v2",
        "status": "ready_for_local_educational_sft",
        "pipeline_code_sha256": {name: hashlib.sha256(
            (Path(__file__).resolve().parents[1] / name).read_bytes()).hexdigest()
            for name in ["scripts/build_source_sft_dataset.py", "src/triage_poc/source_sft.py",
                         "src/triage_poc/sft_authoring_queue.py",
                         "src/triage_poc/anonymization.py"]},
        "run_id": args.run_id,
        "code_revision": args.code_revision,
        "previous_canonical_sha256": hashlib.sha256(
            args.previous_canonical.read_bytes()).hexdigest(),
        "mcq_options": "source_choices_preserved_before_anonymization",
        "long_content_policy": "rejected_not_truncated",
        "split_policy": "preserve_previous_source_record_assignments",
        "record_count": len(records),
        "source_counts": summary["source_counts"],
        "language_counts": summary["language_counts"],
        "split_counts": summary["split_counts"],
        "triage_label_count": summary["triage_label_count"],
        "quality_counts": {
            "source_provided_answers": len(records),
            "direct_identifier_anonymization_passed": len(records),
            "clinical_review_not_performed": len(records),
            "content_truncated": sum(
                bool(record["transformation"]["content_truncated"]) for record in records
            ),
            "unique_record_ids": len({record["record_id"] for record in records}),
            "unique_normalized_questions": len(set(normalized_questions)),
        },
        "source_audits": summary["source_audits"],
        "artifacts": {
            "canonical": canonical,
            "train_qwen3": train,
            "validation_qwen3": validation,
        },
        "source_split_policy": {
            "mediqal": "upstream train only; upstream validation and test excluded",
            "frenchmedmcqa": "rebuilt train only; rebuilt validation and test excluded",
            "medquad": "no upstream split; deterministic derived split",
        },
        "anonymization_policy": {
            "entities": list(SOURCE_DIRECT_IDENTIFIER_ENTITIES),
            "excluded_contextual_entities": ["PERSON", "LOCATION", "DATE_TIME"],
            "reason": (
                "Generic NER produced destructive false positives on disease, drug, anatomy, "
                "and medical organization names in public educational QA corpora."
            ),
        },
        "dpo_source": {
            "dataset": "TsinghuaC3I/UltraMedical-Preference",
            "included_in_sft": False,
            "planned_use": "separate DPO stage",
        },
        "limits": [
            "The records teach medical question answering, not clinically validated triage labels.",
            "No clinical review was performed.",
            "The direct-identifier Presidio scan is a technical privacy control, not RGPD "
            "certification or full de-identification.",
            "The test split is stored only in the canonical artifact and is never "
            "rendered for training.",
        ],
    }
    manifest["source_manifest_counts"] = dict(
        sorted(Counter(record["source"]["source_manifest_id"] for record in records).items())
    )
    args.manifest_output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"Source SFT ready: records={len(records)}, train={len(train_records)}, "
        f"validation={len(validation_records)}, test={summary['split_counts']['test']}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
