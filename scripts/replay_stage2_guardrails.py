#!/usr/bin/env python3
"""Replay proposed guardrails over saved endpoint outputs without new inference."""

import argparse
import json
from pathlib import Path

from triage_poc.guardrail_replay import summarize_guardrail_replay
from triage_poc.safety_evaluation import load_reports


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenarios", required=True, type=Path)
    parser.add_argument("--report", action="append", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Choose a fresh output path.")
    summary = summarize_guardrail_replay(
        json.loads(args.scenarios.read_text()), load_reports(args.report)
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({
        "status": summary["status"],
        "models": {
            key: value["guardrail_status_counts"] for key, value in summary["models"].items()
        },
    }))


if __name__ == "__main__":
    main()
