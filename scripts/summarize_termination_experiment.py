#!/usr/bin/env python3
"""Produce a text-free report from the archived termination micro-run."""
import argparse
import json
from pathlib import Path

from triage_poc.comparison import sha256
from triage_poc.termination_report import summarize_termination_run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.run_directory
    summary = json.loads((root / "summary.json").read_text())
    stages = {stage: list(map(json.loads, (root / f"{stage}.jsonl").read_text().splitlines()))
              for stage in ("before", "after", "reloaded")}
    report = summarize_termination_run(summary, stages)
    report["input_sha256"] = {name: sha256(root / name) for name in
                              ("summary.json", "before.jsonl", "after.jsonl", "reloaded.jsonl")}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
