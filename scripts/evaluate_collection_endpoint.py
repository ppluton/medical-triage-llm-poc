#!/usr/bin/env python3
"""Evaluate synthetic multi-turn collection on an authorized loopback API."""
import argparse
import json
import os
from pathlib import Path

import httpx

from triage_poc.dialogue_evaluation import evaluate_dialogue


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenarios", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Fresh dialogue output required")
    scenarios = json.loads(args.scenarios.read_text())
    if not scenarios or any(row.get("synthetic") is not True for row in scenarios):
        raise ValueError("Synthetic dialogue fixtures required")
    headers = {"Authorization": "Bearer " + os.environ["TRIAGE_API_TOKEN"]}
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=90,
                      follow_redirects=False, headers=headers) as client:
        dialogues = [evaluate_dialogue(client, row) for row in scenarios]
    report = {"status": "passed" if all(d["status"] == "passed" for d in dialogues) else "failed",
              "dialogues": dialogues, "records": [r for d in dialogues for r in d["records"]],
              "clinical_validation": False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "turns": len(report["records"])}))
    raise SystemExit(0 if report["status"] == "passed" else 1)


if __name__ == "__main__":
    main()
