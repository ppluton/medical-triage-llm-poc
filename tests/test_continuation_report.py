import json
import sys

import pytest

from scripts.summarize_sft_pilot import main
from triage_poc.comparison import sha256


def test_report_distinguishes_resume_start_from_base(tmp_path, monkeypatch, capsys):
    canonical = tmp_path / "canonical.jsonl"
    canonical.write_text(
        json.dumps(
            {
                "record_id": "v",
                "split": "validation",
                "response": "alpha",
                "source": {"source_dataset": "synthetic"},
            }
        )
        + "\n"
    )
    cfg = {
        "dataset_sha256": sha256(canonical),
        "pilot_stop_after_steps": 150,
        "evaluation": {"generation_record_ids": ["v"], "max_new_tokens": 512},
    }
    config = tmp_path / "config.json"
    config.write_text(json.dumps(cfg))
    plan = {"parent_config_sha256": sha256(config), "start_step": 150, "stop_step": 500}
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan))
    summary = {
        "configuration": cfg,
        "mode": "general_pilot_continuation",
        "continuation": plan,
        "steps": 500,
        "test_records_used": 0,
        "changed_adapter_tensors": 1,
    }
    summary_path = tmp_path / "summary.json"
    summary_path.write_text(json.dumps(summary))
    for name, answer in [("base", "beta"), ("resume_start", "alpha"), ("pilot_end", "alpha")]:
        (tmp_path / (name + ".json")).write_text(
            json.dumps(
                {
                    "mean_example_response_nll": 0.1,
                    "records": [
                        {"record_id": "v", "output": answer, "generated_token_ids": [12, 151643]}
                    ],
                }
            )
        )
    output = tmp_path / "report.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "report",
            "--config",
            str(config),
            "--canonical",
            str(canonical),
            "--run",
            str(tmp_path),
            "--output",
            str(output),
            "--continuation-plan",
            str(plan_path),
        ],
    )
    main()
    capsys.readouterr()
    result = json.loads(output.read_text())
    assert result["new_optimizer_steps"] == 350
    assert result["stages"]["base"]["exact_normalized_reference_matches"] == 0
    assert result["resume_start_metrics"]["exact_normalized_reference_matches"] == 1
    summary["mode"] = "training_memorization"
    summary_path.write_text(json.dumps(summary))
    with pytest.raises(ValueError, match="continuation"):
        main()
