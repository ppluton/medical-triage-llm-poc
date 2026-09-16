#!/usr/bin/env python3
"""Review all one-shot reserve outputs under the frozen project rubric."""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from triage_poc.raw_review_assist import review_raw_queue


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--reserve", required=True, type=Path)
    parser.add_argument("--coverage", required=True, type=Path)
    parser.add_argument("--summary", required=True, type=Path)
    args = parser.parse_args()
    if args.coverage.exists() or args.summary.exists():
        raise ValueError("Choose fresh reserve review outputs")
    scenarios = json.loads(args.reserve.read_text())
    outputs = json.loads((args.run / "outputs.json").read_text())
    queue = []
    for scenario, output in zip(scenarios, outputs, strict=True):
        digest = hashlib.sha256(output["output"].encode()).hexdigest()
        queue.append(
            {
                "review_id": hashlib.sha256(
                    f"sft\0{scenario['id']}\0{digest}".encode()
                ).hexdigest()[:24],
                "scenario_id": scenario["id"],
                "expected_level": scenario["expected_level"],
                "request": scenario["request"],
                "raw_output": output["output"],
            }
        )
    coverage = review_raw_queue(queue, reviewer="Codex-assisted final project review")
    counts = Counter()
    for row in coverage["flagged"]:
        counts.update(row["flags"])
    result = {
        "status": "completed_project_review_not_clinical_validation",
        "records": len(queue),
        "flagged_records": len(coverage["flagged"]),
        "clear_records": len(coverage["reviewed_no_flags"]),
        "flag_counts": dict(sorted(counts.items())),
        "reuse_policy": "do_not_tune_or_rerun_from_this_result",
        "clinical_validation": "not_performed",
        "limits": coverage["limits"],
    }
    args.coverage.parent.mkdir(parents=True, exist_ok=True)
    args.coverage.write_text(json.dumps(coverage, ensure_ascii=False, indent=2) + "\n")
    args.summary.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
