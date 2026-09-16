#!/usr/bin/env python3
"""Apply bounded model-hidden project-review assistance to every raw v43 output."""

import argparse
import json
from pathlib import Path

from triage_poc.raw_review_assist import review_raw_queue


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--reviewer", default="Codex-assisted project review")
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Choose a fresh review coverage output")
    coverage = review_raw_queue(json.loads(args.queue.read_text()), reviewer=args.reviewer)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(coverage, ensure_ascii=False, indent=2) + "\n")
    print(
        json.dumps(
            {
                "reviewed": len(coverage["reviewed_no_flags"]) + len(coverage["flagged"]),
                "flagged": len(coverage["flagged"]),
                "clear": len(coverage["reviewed_no_flags"]),
            }
        )
    )


if __name__ == "__main__":
    main()
