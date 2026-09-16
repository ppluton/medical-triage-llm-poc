#!/usr/bin/env python3
"""Recompute final QA results and verify alignment to the frozen test export."""

import argparse
import json
import math
from pathlib import Path

from triage_poc.comparison import sha256, validate_conversations
from triage_poc.final_selection import select_generation_ids, validate_final_freeze


def verify(directory: Path, test: Path, freeze_path: Path) -> dict:
    freeze = json.loads(freeze_path.read_text())
    validate_final_freeze(freeze, freeze.get("input_hashes", {}))
    if freeze["input_hashes"].get("test") != sha256(test):
        raise ValueError("Test differs from frozen artifact")
    if json.loads((directory / "final_freeze.json").read_text()) != freeze:
        raise ValueError("Saved freeze differs from supplied freeze")
    summary = json.loads((directory / "summary.json").read_text())
    if (
        summary.get("status") != "completed"
        or summary.get("evaluation_split") != "test"
        or summary.get("test_records_used") != 500
        or summary.get("optimizer_steps") != 0
    ):
        raise ValueError("Completed final evaluation without training required")
    for name, digest in (("test", sha256(test)), ("final_freeze", sha256(freeze_path))):
        if summary["input_hashes"].get(name) != digest:
            raise ValueError("Summary input hash mismatch")
    if summary["script_sha256"] != freeze["input_hashes"].get("runner"):
        raise ValueError("Runner differs from freeze")
    if summary["package_versions"] != freeze["package_versions"]:
        raise ValueError("Runtime differs from freeze")
    for name in ("sft_manifest", "data_manifest"):
        if summary["input_hashes"].get(name) != freeze["input_hashes"].get(name):
            raise ValueError("Model or dataset manifest differs from freeze")
    if summary["dpo_artifact"]["run_summary_sha256"] != freeze["input_hashes"].get("dpo_summary"):
        raise ValueError("DPO summary differs from freeze")
    rows = [json.loads(line) for line in test.read_text().splitlines()]
    validate_conversations(rows)
    if len(rows) != 500:
        raise ValueError("Exactly 500 test examples required")
    ids = [row["record_id"] for row in rows]
    selected = select_generation_ids(ids)
    if json.loads((directory / "selected_ids.json").read_text()) != selected:
        raise ValueError("Saved generation selection differs from deterministic selection")
    metrics = {}
    for stage in ("base", "sft", "dpo"):
        result = json.loads((directory / f"{stage}.json").read_text())
        if (
            [row["record_id"] for row in result["losses"]] != ids
            or [row["record_id"] for row in result["qa"]] != selected
            or result["triage"] != []
        ):
            raise ValueError("Model observations do not match final population")
        values = [row["response_nll"] for row in result["losses"]]
        if any(
            type(value) not in (int, float) or not math.isfinite(value) or value < 0
            for value in values
        ):
            raise ValueError("Invalid response loss")
        for row in result["qa"]:
            tokens = row.get("generated_token_ids")
            latency = row.get("latency_ms")
            if (
                not isinstance(row.get("output"), str)
                or not isinstance(tokens, list)
                or not 1 <= len(tokens) <= 512
                or any(type(token) is not int or token < 0 for token in tokens)
                or type(latency) not in (int, float)
                or not math.isfinite(latency)
                or latency < 0
            ):
                raise ValueError("Incomplete generation observation")
            if type(row["eos_terminated"]) is not bool:
                raise ValueError("Invalid reported EOS flag")
        recomputed = {
            "mean_example_response_nll": sum(values) / len(values),
            "loss_records": len(values),
            "qa_eos_terminated": sum(row["eos_terminated"] for row in result["qa"]),
            "triage": None,
        }
        if recomputed != summary["comparison"][stage]:
            raise ValueError("Final summary differs from saved observations")
        metrics[stage] = recomputed
    return {
        "status": "final_saved_metrics_recomputed",
        "comparison": metrics,
        "test_records": 500,
        "generated_records_per_model": 50,
        "artifact_hashes": {
            path.name: sha256(path)
            for path in [
                directory / f"{name}.json"
                for name in ("summary", "base", "sft", "dpo", "selected_ids", "final_freeze")
            ]
        },
        "limits": [
            "Saved observations checked; inference is not independently repeated.",
            "EOS flags are reported, not recomputed from tokenizer.",
            "No clinical or semantic accuracy inferred from response loss.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("run", "test", "freeze", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Fresh proof output required")
    result = verify(args.run, args.test, args.freeze)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
