#!/usr/bin/env python3
"""Expand explicit line-by-line review coverage into safety scorer decisions."""

import argparse
import json
from pathlib import Path

from triage_poc.safety_evaluation import finalize_review_decisions


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", required=True, type=Path)
    parser.add_argument("--coverage", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Choose a fresh output path.")
    decisions = finalize_review_decisions(
        json.loads(args.queue.read_text()), json.loads(args.coverage.read_text())
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(decisions, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"reviewed_records": len(decisions)}))


if __name__ == "__main__":
    main()
