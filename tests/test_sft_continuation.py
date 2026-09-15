import json

import pytest

from triage_poc.comparison import sha256
from triage_poc.sft_continuation import validate_continuation
from triage_poc.sft_pilot import require_complete_checkpoint


def fixture(tmp_path):
    checkpoint = tmp_path / "trainer/checkpoint-150"
    checkpoint.mkdir(parents=True)
    for name in (
        "adapter_model.safetensors",
        "optimizer.pt",
        "scheduler.pt",
        "rng_state.pth",
        "scaler.pt",
    ):
        (checkpoint / name).write_bytes(b"synthetic")
    (checkpoint / "trainer_state.json").write_text(json.dumps({"global_step": 150}))
    hashes = require_complete_checkpoint(checkpoint, 150)
    cfg = {"synthetic": True}
    summary = tmp_path / "summary.json"
    summary.write_text(
        json.dumps(
            {"mode": "pilot", "steps": 150, "configuration": cfg, "checkpoint_hashes": hashes}
        )
    )
    plan = {
        "start_step": 150,
        "stop_step": 500,
        "training_seconds": 1800,
        "checkpoint_hashes": hashes,
        "source_summary_sha256": sha256(summary),
        "scaler_sha256": sha256(checkpoint / "scaler.pt"),
    }
    return checkpoint, cfg, plan


def test_accepts_exact_parent_and_rejects_changed_state(tmp_path):
    checkpoint, cfg, plan = fixture(tmp_path)
    assert validate_continuation(checkpoint, cfg, plan) == plan["checkpoint_hashes"]
    (checkpoint / "optimizer.pt").write_bytes(b"changed")
    with pytest.raises(ValueError, match="hashes changed"):
        validate_continuation(checkpoint, cfg, plan)


def test_rejects_new_budget_or_different_data(tmp_path):
    checkpoint, cfg, plan = fixture(tmp_path)
    with pytest.raises(ValueError, match="unchanged"):
        validate_continuation(checkpoint, {"different": True}, plan)
    plan["stop_step"] = 1000
    with pytest.raises(ValueError, match="150-to-500"):
        validate_continuation(checkpoint, cfg, plan)


def test_rejects_memorization_checkpoint(tmp_path):
    checkpoint, cfg, plan = fixture(tmp_path)
    summary = checkpoint.parent.parent / "summary.json"
    data = json.loads(summary.read_text())
    data["mode"] = "training_memorization"
    summary.write_text(json.dumps(data))
    plan["source_summary_sha256"] = sha256(summary)
    with pytest.raises(ValueError, match="general pilot"):
        validate_continuation(checkpoint, cfg, plan)
