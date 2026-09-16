#!/usr/bin/env python3
"""Prepare a deterministic blinded safety-review queue from endpoint reports."""

import argparse
import json
from pathlib import Path

from triage_poc.safety_evaluation import (
    load_reports,
    prepare_blinded_review_queue,
    prepare_common_success_blinded_review_queue,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenarios", required=True, type=Path)
    parser.add_argument("--report", action="append", required=True)
    parser.add_argument("--queue", required=True, type=Path)
    parser.add_argument("--key", required=True, type=Path)
    parser.add_argument("--coverage", type=Path)
    parser.add_argument("--common-success-only", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    outputs = [args.queue, args.key, *([args.coverage] if args.coverage else [])]
    if any(path.exists() for path in outputs):
        raise ValueError("Review queue, key and coverage paths must be fresh.")
    scenarios = json.loads(args.scenarios.read_text())
    reports = load_reports(args.report)
    if args.common_success_only:
        if args.coverage is None:
            raise ValueError("Common-success review requires --coverage.")
        queue, key, coverage = prepare_common_success_blinded_review_queue(
            scenarios, reports, seed=args.seed
        )
    else:
        queue, key = prepare_blinded_review_queue(scenarios, reports, seed=args.seed)
        coverage = None
    args.queue.parent.mkdir(parents=True, exist_ok=True)
    args.key.parent.mkdir(parents=True, exist_ok=True)
    args.queue.write_text(json.dumps(queue, ensure_ascii=False, indent=2) + "\n")
    args.key.write_text(json.dumps(key, ensure_ascii=False, indent=2) + "\n")
    if args.coverage and coverage:
        args.coverage.parent.mkdir(parents=True, exist_ok=True)
        args.coverage.write_text(json.dumps(coverage, ensure_ascii=False, indent=2) + "\n")
    print(
        json.dumps(
            {
                "review_records": len(queue),
                "key_records": len(key),
                "seed": args.seed,
                "omitted_scenarios": len(coverage["omissions"]) if coverage else 0,
            }
        )
    )


if __name__ == "__main__":
    main()
