import json
from pathlib import Path

import pytest

from triage_poc.sft_pilot import PilotBudget, require_complete_checkpoint, validate_pilot_config


def test_budget_stops_on_time_or_steps():
    now = [0]
    budget = PilotBudget(150, 1800, lambda: now[0])
    with pytest.raises(ValueError):
        budget.reached(0)
    budget.start()
    assert not budget.reached(149)
    assert budget.reached(150)
    now[0] = 1800
    assert budget.reached(1)


def test_weights_only_checkpoint_is_rejected(tmp_path):
    (tmp_path / "adapter_model.safetensors").write_bytes(b"synthetic")
    with pytest.raises(ValueError, match="Incomplete"):
        require_complete_checkpoint(tmp_path, 2)


def test_pilot_config_keeps_fixed_horizon_and_no_auto_full_run():
    config = json.loads(Path("configs/sft-v2.1-pilot.json").read_text())
    validate_pilot_config(config)
    config["scheduler_horizon_steps"] = config["pilot_stop_after_steps"]
    with pytest.raises(ValueError, match="horizon"):
        validate_pilot_config(config)


def test_pilot_preflight_needs_no_model_and_rejects_mutated_data(tmp_path, monkeypatch, capsys):
    import hashlib
    import sys

    from scripts.run_source_sft_pilot import main

    config = json.loads(Path("configs/sft-v2.1-pilot.json").read_text())
    for split in ("train", "validation"):
        row = {
            "record_id": split,
            "messages": [
                {"role": "system", "content": "Synthetic fixture."},
                {"role": "user", "content": "Return alpha."},
                {"role": "assistant", "content": "alpha"},
            ],
        }
        file = tmp_path / f"{split}-qwen3.jsonl"
        file.write_text(json.dumps(row) + "\n")
        config["artifact_hashes"][f"{split}_qwen3"] = hashlib.sha256(file.read_bytes()).hexdigest()
    config.update(training_records=1, validation_records=1)
    config["evaluation"].update(generation_record_ids=["validation"], generation_records=1)
    (tmp_path / "tokenizer.json").write_text("{}")
    config["tokenizer_files_sha256"] = {"tokenizer.json": hashlib.sha256(b"{}").hexdigest()}
    file = tmp_path / "config.json"
    file.write_text(json.dumps(config))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "pilot",
            "--config",
            str(file),
            "--data",
            str(tmp_path),
            "--tokenizer",
            str(tmp_path),
            "--output",
            str(tmp_path / "never-created"),
        ],
    )
    main()
    assert "preflight_passed_not_launched" in capsys.readouterr().out
    assert not (tmp_path / "never-created").exists()
    (tmp_path / "train-qwen3.jsonl").write_text("{}\n")
    with pytest.raises(ValueError, match="artifact changed"):
        main()
