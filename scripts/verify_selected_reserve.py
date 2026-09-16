#!/usr/bin/env python3
"""Recompute and verify the one-shot selected-model reserve result."""

import argparse
import json
import math
from collections import Counter
from pathlib import Path

from triage_poc.comparison import sha256
from triage_poc.model_snapshot import (
    EXPECTED_BASE_MANIFEST_SHA256,
    EXPECTED_BASE_MODEL_SHA256,
    EXPECTED_BASE_REVISION,
)
from triage_poc.triage_probe import score_outputs


def verify(run: Path, reserve: Path, manifest: Path, selection: Path) -> dict:
    summary = json.loads((run / "summary.json").read_text())
    outputs = json.loads((run / "outputs.json").read_text())
    scenarios = json.loads(reserve.read_text())
    decision = json.loads(selection.read_text())
    frozen = json.loads(manifest.read_text())
    if (
        summary.get("status") != "completed_one_shot_reserve"
        or summary.get("optimizer_steps") != 0
        or summary.get("selected_variant") != "sft"
        or summary.get("reserve_records_used") != 18
        or summary.get("development_records_used") != 0
        or summary.get("qa_test_records_used") != 0
    ):
        raise ValueError("Completed SFT-only reserve result without training is required")
    if (
        decision.get("selected_variant") != "sft"
        or decision.get("held_out_reserve_used") is not False
    ):
        raise ValueError("The pre-reserve SFT decision is required")
    if summary.get("selection_decision_sha256") != sha256(selection):
        raise ValueError("Selection decision checksum mismatch")
    if summary.get("reserve_manifest_sha256") != sha256(manifest):
        raise ValueError("Reserve manifest checksum mismatch")
    if not (
        summary.get("reserve_sha256")
        == sha256(reserve)
        == frozen["artifact"]["sha256"]
    ):
        raise ValueError("Reserve checksum mismatch")
    base = summary.get("base_snapshot", {})
    if base != {
        "revision": EXPECTED_BASE_REVISION,
        "model_sha256": EXPECTED_BASE_MODEL_SHA256,
        "manifest_sha256": EXPECTED_BASE_MANIFEST_SHA256,
        "license": "Apache-2.0",
        "files_verified": 11,
    }:
        raise ValueError("Base snapshot verification differs from the pinned contract")
    if summary.get("dpo_artifact", {}).get("status") != "not_loaded_selected_variant_sft":
        raise ValueError("DPO must remain unloaded in the selected SFT reserve run")
    if len(scenarios) != 18 or [row.get("id") for row in outputs] != [
        row.get("id") for row in scenarios
    ]:
        raise ValueError("Reserve output coverage or order mismatch")
    recomputed = score_outputs(scenarios, outputs)
    if recomputed != summary.get("metrics"):
        raise ValueError("Saved reserve metrics differ from observations")

    repetitions, latencies = [], []
    eos = caps = 0
    for row in outputs:
        tokens = row.get("generated_token_ids")
        latency = row.get("latency_ms")
        if (
            not isinstance(tokens, list)
            or not tokens
            or len(tokens) > 512
            or not isinstance(latency, (int, float))
            or not math.isfinite(latency)
            or latency < 0
        ):
            raise ValueError("Invalid saved reserve generation")
        eos += row.get("eos_terminated") is True
        caps += len(tokens) == 512
        latencies.append(float(latency))
        grams = Counter(tuple(tokens[i : i + 4]) for i in range(len(tokens) - 3))
        repetitions.append(
            sum(count - 1 for count in grams.values()) / max(1, sum(grams.values()))
        )
    ordered = sorted(latencies)
    return {
        "status": "one_shot_reserve_recomputed",
        "selected_variant": "sft",
        "records": len(outputs),
        "valid_schema": recomputed["valid_schema"],
        "agreement_on_all_records": recomputed["agreement_on_all_records"],
        "eos_terminated": eos,
        "reached_token_cap": caps,
        "mean_repeated_token_4gram_fraction": sum(repetitions) / len(repetitions),
        "latency_ms_p50": ordered[len(ordered) // 2],
        "latency_ms_p95": ordered[math.ceil(0.95 * len(ordered)) - 1],
        "artifact_hashes": {
            "summary.json": sha256(run / "summary.json"),
            "outputs.json": sha256(run / "outputs.json"),
        },
        "reuse_policy": "do_not_tune_or_rerun_from_this_result",
        "clinical_validation": "not_performed",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--reserve", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--selection", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Choose a fresh verification output")
    result = verify(args.run, args.reserve, args.manifest, args.selection)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
