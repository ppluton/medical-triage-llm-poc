#!/usr/bin/env python3
"""Fail closed unless a selected SFT file is synthetic and governance-approved."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from triage_poc.training_preflight import TrainingPreflightError, require_approved_manifests


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--split", required=True, choices=("train", "validation"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_directory = Path(__file__).resolve().parents[1] / "data" / "manifests"
    require_approved_manifests(manifest_directory, [args.manifest])

    all_records = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(all_records, list):
        raise TrainingPreflightError("A synthetic SFT input must contain at least one record.")
    records = [record for record in all_records if record.get("split") == args.split]
    if not records:
        raise TrainingPreflightError(f"No records found for split '{args.split}'.")

    expected_manifest_id = Path(args.manifest).stem
    invalid = [
        record.get("record_id", "unknown")
        for record in records
        if record.get("task_type") != "sft"
        or record.get("data_origin") != "synthetic"
        or record.get("source", {}).get("source_manifest_id") != expected_manifest_id
        or record.get("quality", {}).get("pii_anonymization_status") != "passed"
    ]
    if invalid:
        raise TrainingPreflightError(
            "Synthetic technical run rejected records: " + ", ".join(invalid)
        )

    print(
        f"Synthetic technical preflight passed: {len(records)} {args.split} record(s), "
        f"manifest={args.manifest}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
