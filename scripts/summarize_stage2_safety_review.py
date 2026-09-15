#!/usr/bin/env python3
"""Summarize automatic and reviewed stage-2 safety checks."""

import argparse
import json
from pathlib import Path

from triage_poc.safety_evaluation import load_reports, summarize_safety_evaluation


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenarios", required=True, type=Path)
    parser.add_argument("--report", action="append", required=True)
    parser.add_argument("--reviews", required=True, type=Path)
    parser.add_argument("--key", required=True, type=Path)
    parser.add_argument("--gates", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Choose a fresh output path.")
    summary = summarize_safety_evaluation(
        json.loads(args.scenarios.read_text()),
        load_reports(args.report),
        json.loads(args.reviews.read_text()),
        json.loads(args.key.read_text()),
        json.loads(args.gates.read_text()),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({
        "status": summary["status"],
        "models": {key: value["status"] for key, value in summary["models"].items()},
    }))


if __name__ == "__main__":
    main()
