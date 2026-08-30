#!/usr/bin/env python3
"""Prepare an anonymized MedQuAD source queue for clinical scenario authoring."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from triage_poc.anonymization import TextAnonymizer
from triage_poc.medquad_audit import build_medquad_review_queue


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--limit", type=int, default=200)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    queue = build_medquad_review_queue(
        args.repository,
        TextAnonymizer(),
        limit=args.limit,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(queue, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        "MedQuAD authoring queue prepared: "
        f"records={queue['record_count']}, "
        f"rejected_residual_pii={queue['rejected_residual_pii']}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
