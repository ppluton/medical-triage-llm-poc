#!/usr/bin/env python3
"""Recompute matched comparison metrics from complete saved development outputs."""

import argparse
import json
import math
from collections import Counter
from pathlib import Path

from triage_poc.comparison import sha256
from triage_poc.pilot_report import normalize_answer
from triage_poc.triage_probe import score_outputs


def verify(directory, validation, prior_qa, scenarios):
    summary = json.loads((directory / "summary.json").read_text())
    if (
        summary["status"] != "completed"
        or summary["optimizer_steps"] != 0
        or summary["test_records_used"] != 0
    ):
        raise ValueError("Completed evaluation without training or test use required")
    for name, path in (
        ("validation", validation),
        ("prior_qa", prior_qa),
        ("scenarios", scenarios),
    ):
        if sha256(path) != summary["input_hashes"][name]:
            raise ValueError("Input checksum mismatch: " + name)
    validation_rows = [json.loads(line) for line in validation.read_text().splitlines()]
    ids = [row["record_id"] for row in validation_rows]
    references = {
        row["record_id"]: row["messages"][-1]["content"] for row in validation_rows
    }
    qa_ids = [row["record_id"] for row in json.loads(prior_qa.read_text())["records"]]
    cases = json.loads(scenarios.read_text())
    if len(ids) != 479 or len(set(ids)) != 479 or len(qa_ids) != 30 or len(set(qa_ids)) != 30:
        raise ValueError("Frozen validation populations required")
    if not set(qa_ids) <= set(ids) or len(cases) != 18 or len({r["id"] for r in cases}) != 18:
        raise ValueError("Frozen QA and triage alignment required")
    if any(r.get("synthetic") is not True or r.get("split") != "development" for r in cases):
        raise ValueError("Synthetic development scenarios required")
    results = {}
    for stage in ("base", "sft", "dpo"):
        data = json.loads((directory / f"{stage}.json").read_text())
        if [r["record_id"] for r in data["losses"]] != ids or [
            r["record_id"] for r in data["qa"]
        ] != qa_ids:
            raise ValueError("Missing, duplicated or reordered model observations")
        values = [r["response_nll"] for r in data["losses"]]
        if any(not math.isfinite(v) or v < 0 for v in values):
            raise ValueError("Invalid loss measurement")
        repetitions = []
        exact = empty = caps = 0
        for row in data["qa"]:
            tokens = row.get("generated_token_ids")
            output = row.get("output")
            if (
                not isinstance(tokens, list)
                or not tokens
                or len(tokens) > 512
                or not isinstance(output, str)
            ):
                raise ValueError("Invalid saved QA generation")
            exact += normalize_answer(output) == normalize_answer(references[row["record_id"]])
            empty += not output.strip()
            caps += len(tokens) == 512
            grams = Counter(tuple(tokens[i : i + 4]) for i in range(len(tokens) - 3))
            repetitions.append(
                sum(count - 1 for count in grams.values()) / max(1, sum(grams.values()))
            )
        metrics = {
            "mean_example_response_nll": sum(values) / len(values),
            "loss_records": len(values),
            "qa_eos_terminated": sum(r["eos_terminated"] for r in data["qa"]),
            "triage": score_outputs(cases, data["triage"]),
        }
        if metrics != summary["comparison"][stage]:
            raise ValueError("Summary differs from saved observations: " + stage)
        critical = [d for d in metrics["triage"]["details"] if d["expected_level"] == "maximum"]
        results[stage] = {
            "mean_example_response_nll": metrics["mean_example_response_nll"],
            "qa_eos_terminated": metrics["qa_eos_terminated"],
            "qa_reached_token_cap": caps,
            "qa_exact_normalized_reference_matches": exact,
            "qa_empty_outputs": empty,
            "qa_mean_repeated_token_4gram_fraction": sum(repetitions) / len(repetitions),
            "triage_valid_schema": metrics["triage"]["valid_schema"],
            "triage_agreement_on_all_records": metrics["triage"]["agreement_on_all_records"],
            "critical_total": len(critical),
            "critical_valid_maximum": sum(d["predicted_level"] == "maximum" for d in critical),
        }
    return {
        "status": "saved_metrics_recomputed",
        "comparison": results,
        "artifact_hashes": {
            p.name: sha256(p)
            for p in [directory / f"{s}.json" for s in ("summary", "base", "sft", "dpo")]
        },
        "limits": [
            "Checks saved observations, not independent execution or clinical validity.",
            "QA EOS flags are reported by the runner; semantic quality requires review.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("run", "validation", "prior-qa", "scenarios", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Fresh report path required")
    result = verify(args.run, args.validation, args.prior_qa, args.scenarios)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
