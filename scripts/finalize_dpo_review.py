#!/usr/bin/env python3
"""Create a lineage-bound DPO dataset with finalized educational review metadata."""

import argparse
import json
from pathlib import Path

from triage_poc.dpo_review import finalize_dpo_review


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--sft-manifest", required=True, type=Path)
    parser.add_argument("--decision", required=True, type=Path)
    parser.add_argument("--decision-id", required=True)
    parser.add_argument("--review-date", required=True)
    args = parser.parse_args()
    manifest = finalize_dpo_review(
        args.source,
        args.output,
        sft_manifest_path=args.sft_manifest,
        decision_path=args.decision,
        decision_id=args.decision_id,
        review_date=args.review_date,
    )
    print(json.dumps({
        "status": manifest["status"],
        "manifest_id": manifest["manifest_id"],
        "artifacts": manifest["artifacts"],
        "sft_protected_records": manifest["sft_protected_records"],
    }))


if __name__ == "__main__":
    main()
