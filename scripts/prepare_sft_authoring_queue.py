#!/usr/bin/env python3
"""Generate the governed 5,000-item SFT authoring queue and review batches."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from jsonschema import Draft202012Validator

from triage_poc.anonymization import TextAnonymizer
from triage_poc.sft_authoring_queue import (
    RISK_FAMILY_CANDIDATE_QUOTAS,
    SOURCE_ANCHOR_QUOTAS,
    build_sft_authoring_queue,
    iter_frenchmedmcqa_anchors,
    iter_mediqa_anchors,
    iter_medquad_anchors,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--medquad-repository", required=True, type=Path)
    parser.add_argument("--mediqa-repository", required=True, type=Path)
    parser.add_argument("--frenchmedmcqa-rebuilt", required=True, type=Path)
    parser.add_argument("--output-directory", required=True, type=Path)
    parser.add_argument("--schema", required=True, type=Path)
    parser.add_argument("--manifest-output", required=True, type=Path)
    parser.add_argument("--code-revision", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--batch-size", type=int, default=100)
    return parser.parse_args()


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> str:
    content = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
    path.write_text(content, encoding="utf-8")
    return hashlib.sha256(content.encode()).hexdigest()


def main() -> int:
    args = parse_args()
    if args.batch_size <= 0:
        raise ValueError("batch-size must be positive.")
    schema = json.loads(args.schema.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    queue = build_sft_authoring_queue(
        {
            "medquad": iter_medquad_anchors(args.medquad_repository),
            "mediqa2019": iter_mediqa_anchors(args.mediqa_repository),
            "frenchmedmcqa": iter_frenchmedmcqa_anchors(args.frenchmedmcqa_rebuilt),
        },
        TextAnonymizer(),
        code_revision=args.code_revision,
        run_id=args.run_id,
    )
    records = queue["records"]
    for record in records:
        validator.validate(record)

    args.output_directory.mkdir(parents=True, exist_ok=True)
    queue_path = args.output_directory / "sft-authoring-queue-v1.jsonl"
    queue_sha256 = _write_jsonl(queue_path, records)
    batches = []
    for offset in range(0, len(records), args.batch_size):
        batch_number = offset // args.batch_size + 1
        batch_path = args.output_directory / f"review-batch-{batch_number:03d}.jsonl"
        batch_rows = records[offset : offset + args.batch_size]
        batches.append(
            {
                "path": batch_path.name,
                "record_count": len(batch_rows),
                "sha256": _write_jsonl(batch_path, batch_rows),
            }
        )

    index_rows = [
        {
            "candidate_id": record["candidate_id"],
            "bilingual_group_id": record["bilingual_group_id"],
            "source_manifest_id": record["source"]["source_manifest_id"],
            "source_record_id": record["source"]["source_record_id"],
            "requested_language": record["requested_language"],
            "requested_risk_family": record["requested_risk_family"],
            "content_sha256": hashlib.sha256(
                json.dumps(record, ensure_ascii=False, sort_keys=True).encode()
            ).hexdigest(),
        }
        for record in records
    ]
    index_path = args.output_directory / "sft-authoring-index-v1.jsonl"
    index_sha256 = _write_jsonl(index_path, index_rows)
    source_counts = Counter(record["source"]["source_dataset"] for record in records)
    language_counts = Counter(record["requested_language"] for record in records)
    risk_counts = Counter(record["requested_risk_family"] for record in records)
    manifest = {
        "schema_version": "1.0.0",
        "manifest_id": "derived-sft-authoring-queue-v1",
        "status": "authoring_queue_not_training_data",
        "run_id": args.run_id,
        "code_revision": args.code_revision,
        "record_count": len(records),
        "unique_bilingual_groups": len({record["bilingual_group_id"] for record in records}),
        "training_eligible_count": sum(bool(record["training_eligible"]) for record in records),
        "triage_target_present_count": sum(
            record["draft"]["triage_level"] is not None for record in records
        ),
        "split_present_count": sum(record["split"] is not None for record in records),
        "source_anchor_quotas": SOURCE_ANCHOR_QUOTAS,
        "source_candidate_counts": dict(sorted(source_counts.items())),
        "language_counts": dict(sorted(language_counts.items())),
        "risk_family_candidate_quotas": RISK_FAMILY_CANDIDATE_QUOTAS,
        "risk_family_counts": dict(sorted(risk_counts.items())),
        "source_audits": queue["source_audits"],
        "artifacts": {
            "queue": {"path": queue_path.name, "sha256": queue_sha256},
            "text_free_index": {"path": index_path.name, "sha256": index_sha256},
            "review_batches": batches,
        },
        "limits": queue["limits"],
    }
    args.manifest_output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        "SFT authoring queue prepared: "
        f"records={len(records)}, groups={manifest['unique_bilingual_groups']}, "
        f"training_eligible={manifest['training_eligible_count']}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
