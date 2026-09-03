#!/usr/bin/env python3
"""Create a stratified, editable review pilot and a text-free manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from triage_poc.sft_review_batch import (
    build_review_items,
    select_stratified_groups,
    summarize_review_items,
)


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream]


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> str:
    content = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
    path.write_text(content, encoding="utf-8")
    return hashlib.sha256(content.encode()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", required=True, type=Path)
    parser.add_argument("--queue-sha256", required=True)
    parser.add_argument("--candidate-schema", required=True, type=Path)
    parser.add_argument("--review-schema", required=True, type=Path)
    parser.add_argument("--output-directory", required=True, type=Path)
    parser.add_argument("--manifest-output", required=True, type=Path)
    parser.add_argument("--code-revision", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--group-count", type=int, default=50)
    parser.add_argument("--seed", default="sft-review-pilot-v1")
    args = parser.parse_args()

    queue_bytes = args.queue.read_bytes()
    actual_queue_sha256 = hashlib.sha256(queue_bytes).hexdigest()
    if actual_queue_sha256 != args.queue_sha256:
        raise ValueError("Queue SHA-256 does not match the expected manifest value.")

    records = _read_jsonl(args.queue)
    candidate_validator = Draft202012Validator(
        json.loads(args.candidate_schema.read_text(encoding="utf-8"))
    )
    for record in records:
        candidate_validator.validate(record)

    selected = select_stratified_groups(
        records, group_count=args.group_count, seed=args.seed
    )
    review_items = build_review_items(selected)
    review_validator = Draft202012Validator(
        json.loads(args.review_schema.read_text(encoding="utf-8"))
    )
    for item in review_items:
        review_validator.validate(item)

    args.output_directory.mkdir(parents=True, exist_ok=True)
    review_path = args.output_directory / "review-pilot-001.jsonl"
    review_sha256 = _write_jsonl(review_path, review_items)
    summary = summarize_review_items(review_items)
    manifest = {
        "schema_version": "1.0.0",
        "manifest_id": "derived-sft-review-pilot-001-v1",
        "status": "manual_review_not_started",
        "code_revision": args.code_revision,
        "run_id": args.run_id,
        "source_queue": {
            "path": args.queue.name,
            "sha256": actual_queue_sha256,
            "record_count": len(records),
        },
        "selection": {
            "seed": args.seed,
            "group_count": args.group_count,
            "strategy": "proportional_largest_remainder_by_risk_family_and_source",
        },
        **summary,
        "artifact": {"path": review_path.name, "sha256": review_sha256},
        "limits": [
            "All review decisions remain pending.",
            "This pilot does not constitute clinical review or validation.",
            "The local review artifact contains source-grounding text and must stay out of Git.",
        ],
    }
    args.manifest_output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"Review pilot prepared: groups={summary['review_item_count']}, "
        f"candidates={summary['candidate_count']}, status=pending."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
