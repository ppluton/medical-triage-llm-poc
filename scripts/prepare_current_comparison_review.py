#!/usr/bin/env python3
"""Prepare a blind review queue from Base/SFT/DPO raw comparison outputs."""

import argparse
import json
from pathlib import Path

from triage_poc.comparison_review import prepare_all_raw_comparison_review


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--scenarios", required=True, type=Path)
    parser.add_argument("--queue", required=True, type=Path)
    parser.add_argument("--key", required=True, type=Path)
    parser.add_argument("--coverage", required=True, type=Path)
    parser.add_argument("--seed", type=int, default=143)
    args = parser.parse_args()
    if any(path.exists() for path in (args.queue, args.key, args.coverage)):
        raise ValueError("Review queue, key and coverage outputs must be fresh")
    scenarios = json.loads(args.scenarios.read_text())
    outputs = {
        variant: json.loads((args.run / f"{variant}.json").read_text())["triage"]
        for variant in ("base", "sft", "dpo")
    }
    queue, key, coverage = prepare_all_raw_comparison_review(
        scenarios, outputs, seed=args.seed
    )
    args.queue.parent.mkdir(parents=True, exist_ok=True)
    args.queue.write_text(json.dumps(queue, ensure_ascii=False, indent=2) + "\n")
    args.key.write_text(json.dumps(key, ensure_ascii=False, indent=2) + "\n")
    args.coverage.write_text(json.dumps(coverage, ensure_ascii=False, indent=2) + "\n")
    print(
        json.dumps(
            {
                "review_records": len(queue),
                "key_records": len(key),
                "schema_invalid_records": coverage["schema_invalid_records"],
                "seed": args.seed,
            }
        )
    )


if __name__ == "__main__":
    main()
