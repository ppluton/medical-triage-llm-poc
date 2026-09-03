#!/usr/bin/env python3
"""Generate and validate the 5,000-record educational SFT dataset."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from triage_poc.educational_protocol import load_educational_protocol
from triage_poc.educational_sft import generate_educational_sft_records


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-queue", required=True, type=Path)
    parser.add_argument("--candidate-queue-sha256", required=True)
    parser.add_argument("--candidate-schema", required=True, type=Path)
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--protocol-schema", required=True, type=Path)
    parser.add_argument("--record-schema", required=True, type=Path)
    parser.add_argument("--manifest-schema", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--manifest-output", required=True, type=Path)
    parser.add_argument("--code-revision", required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()

    queue_bytes = args.candidate_queue.read_bytes()
    queue_sha256 = hashlib.sha256(queue_bytes).hexdigest()
    if queue_sha256 != args.candidate_queue_sha256:
        raise ValueError("Candidate queue SHA-256 does not match the expected value.")
    candidates = _load_jsonl(args.candidate_queue)
    candidate_validator = Draft202012Validator(
        json.loads(args.candidate_schema.read_text(encoding="utf-8"))
    )
    for candidate in candidates:
        candidate_validator.validate(candidate)

    protocol_bytes = args.protocol.read_bytes()
    protocol_sha256 = hashlib.sha256(protocol_bytes).hexdigest()
    protocol = load_educational_protocol(args.protocol, args.protocol_schema)
    records, summary = generate_educational_sft_records(
        candidates,
        protocol,
        protocol_sha256=protocol_sha256,
        code_revision=args.code_revision,
        run_id=args.run_id,
        dataset_manifest_id="src-educational-sft-protocol-v1",
    )
    if summary["duplicate_content_count"]:
        raise ValueError(
            f"Exact synthetic content duplicates detected: {summary['duplicate_content_count']}."
        )
    record_validator = Draft202012Validator(
        json.loads(args.record_schema.read_text(encoding="utf-8"))
    )
    for record in records:
        record_validator.validate(record)

    group_splits: dict[str, set[str]] = {}
    for record in records:
        group_id = record["protocol"]["grounding_candidate_id"].rsplit("-", 1)[0]
        group_splits.setdefault(group_id, set()).add(record["split"])
    if any(len(splits) != 1 for splits in group_splits.values()):
        raise ValueError("Bilingual group split leakage detected.")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(records, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    args.output.write_text(content, encoding="utf-8")
    artifact_sha256 = hashlib.sha256(content.encode()).hexdigest()
    manifest = {
        "schema_version": "1.0.0",
        "manifest_id": "src-educational-sft-protocol-v1",
        "status": "approved_for_educational_experiment",
        "intended_use": "educational_poc_training_only",
        "artifact": {
            "path": args.output.name,
            "byte_size": len(content.encode()),
            "sha256": artifact_sha256,
        },
        "source_queue": {
            "path": args.candidate_queue.name,
            "sha256": queue_sha256,
            "record_count": len(candidates),
        },
        "protocol": {
            "protocol_id": protocol["protocol_id"],
            "sha256": protocol_sha256,
            "status": protocol["status"],
        },
        "transformation": {
            "pipeline_name": "educational_sft_generator",
            "pipeline_version": "1.0.0",
            "code_revision": args.code_revision,
            "run_id": args.run_id,
        },
        "counts": {
            key: value
            for key, value in summary.items()
            if key
            in {
                "record_count",
                "split_counts",
                "language_counts",
                "label_counts",
                "risk_family_counts",
            }
        },
        "quality": {
            "schema_validation": "passed",
            "group_split_leakage": "passed",
            "duplicate_content_count": summary["duplicate_content_count"],
            "clinical_review_status_counts": summary["clinical_review_status_counts"],
        },
        "clinical_validation": {"performed": False, "claims_allowed": False},
        "limits": [
            "Labels are generated by a proposed educational protocol, not clinical review.",
            "Source references provide provenance but scenarios are template-generated.",
            "The dataset is prohibited for patient care or clinical performance claims.",
        ],
    }
    manifest_validator = Draft202012Validator(
        json.loads(args.manifest_schema.read_text(encoding="utf-8"))
    )
    manifest_validator.validate(manifest)
    args.manifest_output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"Educational SFT dataset generated: records={len(records)}, "
        f"splits={summary['split_counts']}, labels={summary['label_counts']}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
