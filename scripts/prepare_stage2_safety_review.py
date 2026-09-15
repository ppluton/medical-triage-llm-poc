#!/usr/bin/env python3
"""Prepare a deterministic blinded safety-review queue from endpoint reports."""

import argparse
import json
from pathlib import Path

from triage_poc.safety_evaluation import load_reports, prepare_blinded_review_queue


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenarios", required=True, type=Path)
    parser.add_argument("--report", action="append", required=True)
    parser.add_argument("--queue", required=True, type=Path)
    parser.add_argument("--key", required=True, type=Path)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.queue.exists() or args.key.exists():
        raise ValueError("Review queue and key paths must be fresh.")
    scenarios = json.loads(args.scenarios.read_text())
    queue, key = prepare_blinded_review_queue(scenarios, load_reports(args.report), seed=args.seed)
    args.queue.parent.mkdir(parents=True, exist_ok=True)
    args.key.parent.mkdir(parents=True, exist_ok=True)
    args.queue.write_text(json.dumps(queue, ensure_ascii=False, indent=2) + "\n")
    args.key.write_text(json.dumps(key, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"review_records": len(queue), "key_records": len(key), "seed": args.seed}))


if __name__ == "__main__":
    main()
