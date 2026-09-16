#!/usr/bin/env python3
"""Unblind and summarize a completed qualitative stage-2 review."""

import argparse
import json
from pathlib import Path

from triage_poc.safety_evaluation import summarize_qualitative_review


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviews", required=True, type=Path)
    parser.add_argument("--key", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Choose a fresh output path.")
    summary = summarize_qualitative_review(
        json.loads(args.reviews.read_text()), json.loads(args.key.read_text())
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
