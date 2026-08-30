#!/usr/bin/env python3
"""Run a privacy-minimizing Presidio audit on a deterministic MedQuAD sample."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from triage_poc.anonymization import TextAnonymizer
from triage_poc.medquad_audit import audit_presidio_sample


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--sample-per-subset", type=int, default=10)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = audit_presidio_sample(
        args.repository,
        TextAnonymizer(),
        sample_per_subset=args.sample_per_subset,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        "MedQuAD Presidio sample completed: "
        f"samples={report['sample_count']}, "
        f"statuses={report['anonymization_status_counts']}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
