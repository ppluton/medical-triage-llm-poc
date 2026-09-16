#!/usr/bin/env python3
"""Derive an immutable content-isolated candidate without rewriting historical splits."""

import argparse
import json
from collections import Counter
from pathlib import Path

from triage_poc.comparison import sha256
from triage_poc.sft_isolation import cross_split_groups, isolate_groups
from triage_poc.source_sft import render_source_sft_conversation
from triage_poc.source_sft_preflight import validate_source_sft_artifacts


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("audit", "manifest", "artifacts", "output", "manifest-output"):
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--candidate-id", default="derived-source-medical-qa-sft-v2.1")
    p.add_argument("--reviewed-exclusions", type=Path)
    a = p.parse_args()
    if a.output.exists() or a.manifest_output.exists():
        raise ValueError("Only fresh immutable outputs are accepted")
    manifest, rows, _, _ = validate_source_sft_artifacts(
        a.manifest, a.artifacts, audit_candidate=True
    )
    report = json.loads((a.audit / "report.json").read_text())
    if (
        report["input_sha256"] != manifest["artifacts"]["canonical"]["sha256"]
        or report["review_flags"]
    ):
        raise ValueError("Audit does not approve this source artifact for isolation")
    groups = json.loads((a.audit / "groups.json").read_text())
    kept, excluded = isolate_groups(rows, groups)
    if excluded != json.loads((a.audit / "exclusions.json").read_text()):
        raise ValueError("Exclusion decisions differ from the audited groups")
    if cross_split_groups(kept, groups):
        raise ValueError("Content groups still cross splits")
    assert [r for r in rows if r["split"] == "test"] == [r for r in kept if r["split"] == "test"]
    if a.reviewed_exclusions:
        review = json.loads(a.reviewed_exclusions.read_text())
        if review["canonical_sha256"] != manifest["artifacts"]["canonical"]["sha256"]:
            raise ValueError("Review refers to another corpus")
        remove = {r["record_id"] for r in review["exclusions"]}
        eligible = {r["record_id"] for r in kept if r["split"] != "test"}
        if not remove <= eligible:
            raise ValueError("Review may exclude only retained development records")
        kept = [r for r in kept if r["record_id"] not in remove]
        excluded += review["exclusions"]
    a.output.mkdir(parents=True)
    artifacts = {}
    for key, name, records in (
        ("canonical", "source-sft-v2.1.jsonl", kept),
        (
            "train_qwen3",
            "train-qwen3.jsonl",
            [render_source_sft_conversation(r) for r in kept if r["split"] == "train"],
        ),
        (
            "validation_qwen3",
            "validation-qwen3.jsonl",
            [render_source_sft_conversation(r) for r in kept if r["split"] == "validation"],
        ),
    ):
        file = a.output / name
        file.write_text(
            "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in records)
        )
        artifacts[key] = {
            "path": name,
            "sha256": sha256(file),
            "record_count": len(records),
            "byte_size": file.stat().st_size,
        }
    result = {
        "manifest_id": a.candidate_id,
        "schema_version": "1.0.0",
        "status": "candidate_pending_pilot",
        "date": "2026-09-11",
        "parent_manifest_sha256": sha256(a.manifest),
        "parent_canonical_sha256": manifest["artifacts"]["canonical"]["sha256"],
        "record_count": len(kept),
        "triage_label_count": 0,
        "artifacts": artifacts,
        "split_counts": dict(Counter(r["split"] for r in kept)),
        "source_counts": dict(Counter(r["source"]["source_dataset"] for r in kept)),
        "language_counts": dict(Counter(r["language"] for r in kept)),
        "exclusions": excluded,
        "audit_report_sha256": sha256(a.audit / "report.json"),
        "group_keys_sha256": sha256(a.audit / "groups.json"),
        "historical_records_unchanged": True,
        "test_records_unchanged": 500,
        "grouping_policy": "ADR-012",
        "cross_split_content_groups": 0,
        "script_sha256": sha256(Path(__file__)),
        "training_launched": False,
        "limits": [
            "No clinical validation; no guarantee against semantic paraphrases.",
            "Old SFT checkpoints were not trained with this isolation policy.",
        ],
    }
    a.manifest_output.parent.mkdir(parents=True, exist_ok=True)
    a.manifest_output.write_text(json.dumps(result, indent=2) + "\n")
    validate_source_sft_artifacts(a.manifest_output, a.output, audit_candidate=True)
    print(
        json.dumps(
            {
                k: result[k]
                for k in (
                    "record_count",
                    "split_counts",
                    "source_counts",
                    "language_counts",
                    "cross_split_content_groups",
                )
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
