import json

import pytest

from triage_poc.comparison import sha256
from triage_poc.sft_handoff import HANDOFF_FILES, build_sft_handoff


def _fixture(tmp_path):
    run = tmp_path / "run"
    reload = tmp_path / "reload"
    checkpoint = run / "trainer/checkpoint-2"
    checkpoint.mkdir(parents=True)
    reload.mkdir()
    config = {
        "date": "2026-09-16",
        "base_model": "/synthetic/base",
        "base_revision": "a" * 40,
        "dataset_sha256": "b" * 64,
        "pilot_stop_after_steps": 2,
        "training_chat_template_sha256": "",
        "evaluation": {"generation_record_ids": ["one", "two"]},
    }
    for name in HANDOFF_FILES:
        value = (
            json.dumps({"base_model_name_or_path": config["base_model"]})
            if name == "adapter_config.json"
            else f"synthetic {name}"
        )
        (checkpoint / name).write_text(value)
    config["training_chat_template_sha256"] = sha256(checkpoint / "chat_template.jinja")
    for name in ("optimizer.pt", "scheduler.pt", "rng_state.pth"):
        (checkpoint / name).write_text(name)
    (checkpoint / "trainer_state.json").write_text(json.dumps({"global_step": 2}))
    hashes = {
        name: sha256(checkpoint / name)
        for name in (
            "adapter_model.safetensors",
            "optimizer.pt",
            "scheduler.pt",
            "rng_state.pth",
            "trainer_state.json",
        )
    }
    (run / "summary.json").write_text(json.dumps({
        "status": "pilot_completed_pending_quality_review",
        "mode": "pilot",
        "configuration": config,
        "test_records_used": 0,
        "steps": 2,
        "checkpoint_hashes": hashes,
    }))
    (reload / "summary.json").write_text(json.dumps({
        "status": "pilot_fresh_reload_verified",
        "optimizer_steps_executed": 0,
        "test_records_used": 0,
        "configuration": config,
        "checkpoint_hashes": hashes,
        "identical_generations": 2,
        "absolute_loss_delta": 0.0,
    }))
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"artifacts": {"canonical": {"sha256": "b" * 64}}}))
    return run, reload, config_path, manifest, checkpoint


def test_builds_handoff_bound_to_fresh_reload(tmp_path):
    run, reload, config, manifest, checkpoint = _fixture(tmp_path)
    output = tmp_path / "handoff.json"
    result = build_sft_handoff(
        run, reload, config, manifest, output, checkpoint_label="fixture-step-2"
    )
    assert result["files"]["adapter_model.safetensors"] == sha256(
        checkpoint / "adapter_model.safetensors"
    )
    assert result["test_records_used"] == 0
    assert json.loads(output.read_text()) == result


def test_refuses_reload_or_checkpoint_drift(tmp_path):
    run, reload, config, manifest, checkpoint = _fixture(tmp_path)
    value = json.loads((reload / "summary.json").read_text())
    value["optimizer_steps_executed"] = 1
    (reload / "summary.json").write_text(json.dumps(value))
    with pytest.raises(ValueError, match="reload proof"):
        build_sft_handoff(
            run, reload, config, manifest, tmp_path / "handoff.json", checkpoint_label="fixture"
        )
    value["optimizer_steps_executed"] = 0
    (reload / "summary.json").write_text(json.dumps(value))
    (checkpoint / "adapter_model.safetensors").write_text("changed")
    with pytest.raises(ValueError, match="checkpoint hashes"):
        build_sft_handoff(
            run, reload, config, manifest, tmp_path / "other.json", checkpoint_label="fixture"
        )
