#!/usr/bin/env python3
"""Compare the frozen base with verified 50/100/150-step pilot checkpoint outputs."""

import argparse
import json
from pathlib import Path

from triage_poc.comparison import sha256
from triage_poc.pilot_report import summarize_pilot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("config", "canonical", "pilot", "reload", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    cfg = json.loads(args.config.read_text())
    original = json.loads((args.pilot / "summary.json").read_text())
    reload = json.loads((args.reload / "summary.json").read_text())
    if (
        sha256(args.canonical) != cfg["dataset_sha256"]
        or original["configuration"] != cfg
        or reload["configuration"] != cfg
        or reload["status"] != "pilot_fresh_reload_verified"
        or reload["optimizer_steps_executed"] != 0
        or reload["identical_generations"] != cfg["evaluation"]["generation_records"]
        or reload["loss_records"] != cfg["evaluation"]["loss_records"]
        or reload["checkpoint_hashes"] != original["checkpoint_hashes"]
    ):
        raise ValueError("Verified reload of the frozen pilot required")
    refs = {
        r["record_id"]: r
        for r in map(json.loads, args.canonical.read_text().splitlines())
        if r["split"] == "validation"
    }
    baseline = json.loads((args.pilot / "base.json").read_text())
    stages = {}
    files = {}
    for step, name in [
        (50, "checkpoint_50.json"),
        (100, "checkpoint_100.json"),
        (150, "reloaded.json"),
    ]:
        if step != 150:
            local = args.pilot / "trainer" / f"checkpoint-{step}" / "adapter_model.safetensors"
            expected = reload["intermediate_checkpoint_hashes"][str(step)][
                "adapter_model.safetensors"
            ]
            if sha256(local) != expected:
                raise ValueError("Intermediate checkpoint differs from local archive")
        data = json.loads((args.reload / name).read_text())
        report = summarize_pilot(cfg, {"base": baseline, "pilot_end": data}, refs)
        stages["base"] = report["stages"]["base"]
        stages[str(step)] = report["stages"]["pilot_end"]
        files[name] = sha256(args.reload / name)
    result = {
        "status": "checkpoint_comparison_complete_pending_quality_decision",
        "stages": stages,
        "input_sha256": files,
        "reload_summary_sha256": sha256(args.reload / "summary.json"),
        "base_sha256": sha256(args.pilot / "base.json"),
        "full_training_approved": False,
        "clinical_validation": "not_performed",
        "limits": report["limits"][:2],
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
