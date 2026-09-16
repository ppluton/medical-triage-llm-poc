#!/usr/bin/env python3
"""Select SFT or DPO from verified development evidence before opening the reserve."""

import argparse
import json
from pathlib import Path

from triage_poc.candidate_selection import select_candidate
from triage_poc.evaluation_reserve import sha256


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comparison-summary", required=True, type=Path)
    parser.add_argument("--verified-comparison", required=True, type=Path)
    parser.add_argument("--qualitative-summary", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Choose a fresh model-selection output")
    raw = json.loads(args.comparison_summary.read_text())
    if (
        raw.get("status") != "completed"
        or raw.get("optimizer_steps") != 0
        or raw.get("test_records_used") != 0
        or raw.get("evaluation_split") != "validation"
    ):
        raise ValueError("The raw comparison must be completed on development only")
    verified = json.loads(args.verified_comparison.read_text())
    qualitative = json.loads(args.qualitative_summary.read_text())
    decision = select_candidate(verified, qualitative)
    decision.update(
        {
            "comparison_summary_sha256": sha256(args.comparison_summary),
            "verified_comparison_sha256": sha256(args.verified_comparison),
            "qualitative_summary_sha256": sha256(args.qualitative_summary),
        }
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(decision, indent=2) + "\n")
    print(json.dumps(decision, indent=2))


if __name__ == "__main__":
    main()
