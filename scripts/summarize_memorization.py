#!/usr/bin/env python3
"""Verify and summarize the train-only diagnostic without exporting answer text."""

import argparse
import json
from pathlib import Path

from triage_poc.comparison import sha256
from triage_poc.pilot_report import normalize_answer

p = argparse.ArgumentParser(description=__doc__)
for name in ("run", "manifest", "launch", "canonical", "output"):
    p.add_argument("--" + name, type=Path, required=True)
a = p.parse_args()
m = json.loads(a.manifest.read_text())
launch = json.loads(a.launch.read_text())
summary = json.loads((a.run / "summary.json").read_text())
if summary["mode"] != "training_memorization" or summary["memorization"]["manifest"] != m:
    raise ValueError("Wrong experiment or manifest")
if (
    sha256(a.manifest) != launch["manifest_sha256"]
    or summary["script_sha256"] != launch["files_sha256"]["scripts/run_source_sft_pilot.py"]
):
    raise ValueError("Run does not match launched code and manifest")
if sha256(a.canonical) != summary["configuration"]["dataset_sha256"]:
    raise ValueError("Parent corpus changed")
refs = {r["record_id"]: r for r in map(json.loads, a.canonical.read_text().splitlines())}
if any(refs[rid]["split"] != "train" for rid in m["record_ids"]):
    raise ValueError("Held-out record used")
stages = {}
records = []
for stage in ("base", "pilot_end"):
    data = json.loads((a.run / (stage + ".json")).read_text())
    if [r["record_id"] for r in data["records"]] != m["record_ids"]:
        raise ValueError("Generation cohort changed")
    exact, eos = 0, 0
    for r in data["records"]:
        agrees = normalize_answer(r["output"]) == normalize_answer(refs[r["record_id"]]["response"])
        ended = r["generated_token_ids"][-1] == 151643
        exact += agrees
        eos += ended
        records.append(
            {
                "stage": stage,
                "record_id": r["record_id"],
                "exact_reference": agrees,
                "native_eos": ended,
            }
        )
    stages[stage] = {
        "mean_example_train_nll": data["mean_example_response_nll"],
        "exact_answers": exact,
        "eos_terminated": eos,
        "records": len(data["records"]),
    }
    reported = summary["memorization"]["stages"][stage]
    assert all(reported[k] == stages[stage][k] for k in reported)
passed = stages["pilot_end"]["exact_answers"] == 12 and stages["pilot_end"]["eos_terminated"] == 12
result = {
    "date": "2026-09-11",
    "status": "memorization_target_met" if passed else "memorization_target_not_met",
    "stages": stages,
    "records": records,
    "optimizer_steps": summary["steps"],
    "script_sha256": summary["script_sha256"],
    "checkpoint_hashes": summary["checkpoint_hashes"],
    "input_sha256": {
        name: sha256(a.run / name) for name in ("summary.json", "base.json", "pilot_end.json")
    },
    "generalization_measured": False,
    "validation_records_used": 0,
    "test_records_used": 0,
    "limits": m["limits"],
}
a.output.write_text(json.dumps(result, indent=2) + "\n")
print(
    json.dumps(
        {"status": result["status"], "stages": stages, "optimizer_steps": summary["steps"]},
        indent=2,
    )
)
