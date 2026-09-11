#!/usr/bin/env python3
"""Summarize archived paired pilot outputs without publishing source or output texts."""

import argparse
import json
from pathlib import Path

from triage_poc.comparison import sha256
from triage_poc.pilot_report import summarize_pilot


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("config", "canonical", "run", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    cfg = json.loads(a.config.read_text())
    if sha256(a.canonical) != cfg["dataset_sha256"]:
        raise ValueError("Frozen reference corpus changed")
    refs = {
        r["record_id"]: r
        for r in map(json.loads, a.canonical.read_text().splitlines())
        if r["split"] == "validation"
    }
    stages = {s: json.loads((a.run / f"{s}.json").read_text()) for s in ("base", "pilot_end")}
    summary = json.loads((a.run / "summary.json").read_text())
    if (
        summary["configuration"] != cfg
        or summary["test_records_used"] != 0
        or summary["steps"] > cfg["pilot_stop_after_steps"]
    ):
        raise ValueError("Actual pilot does not match the frozen configuration")
    report = summarize_pilot(cfg, stages, refs)
    report.update(
        optimizer_steps=summary["steps"],
        changed_adapter_tensors=summary["changed_adapter_tensors"],
        input_sha256={
            name: sha256(a.run / name) for name in ("base.json", "pilot_end.json", "summary.json")
        },
    )
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
