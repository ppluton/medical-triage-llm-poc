"""Synthetic-file checks for the bounded runner's input gates; no model is loaded."""
import hashlib
import json
import sys

import pytest

from scripts import run_sft_termination_experiment as runner


def setup_inputs(tmp_path, monkeypatch):
    def write(split, count):
        rows = [{"record_id": f"synthetic-{split}-{i}", "messages": [
            {"role": role, "content": f"synthetic {role} content"}
            for role in ("system", "user", "assistant")]} for i in range(count)]
        path = tmp_path / f"{split}.jsonl"
        path.write_text("".join(json.dumps(r) + "\n" for r in rows))
        return path

    train, validation = write("train", 64), write("validation", 3)
    adapter = tmp_path / "adapter"
    adapter.mkdir()
    weights = adapter / "adapter_model.safetensors"
    weights.write_bytes(b"synthetic weights; never loaded in dry-run")
    monkeypatch.setattr(runner, "SFT_SHA256", hashlib.sha256(weights.read_bytes()).hexdigest())
    hashes = {"train": runner.sha256(train), "validation": runner.sha256(validation)}
    monkeypatch.setattr(runner, "SMOKE_HASHES", {"v2": hashes})
    monkeypatch.setattr(sys, "argv", ["runner", "--train", str(train), "--validation",
        str(validation), "--sft-adapter", str(adapter), "--output", str(tmp_path / "output"),
        "--dataset-version", "v2", "--input-scope", "smoke", "--arm", "native-eos", "--dry-run"])
    return train, validation, hashes


def test_smoke_inputs_pass_without_loading_a_model(tmp_path, monkeypatch, capsys):
    setup_inputs(tmp_path, monkeypatch)
    runner.main()
    result = json.loads(capsys.readouterr().out)
    assert result["input_scope"] == "smoke"
    assert (result["train"], result["validation"], result["test_records_used"]) == (64, 3, 0)
    assert not (tmp_path / "output").exists()


def test_changed_input_is_rejected_before_training(tmp_path, monkeypatch):
    train, _, _ = setup_inputs(tmp_path, monkeypatch)
    train.write_text(train.read_text().replace("synthetic user", "changed synthetic user"))
    with pytest.raises(ValueError, match="Training artifact differs"):
        runner.main()


def test_rehashed_incomplete_validation_is_rejected(tmp_path, monkeypatch):
    _, validation, hashes = setup_inputs(tmp_path, monkeypatch)
    validation.write_text("\n".join(validation.read_text().splitlines()[:2]) + "\n")
    hashes["validation"] = runner.sha256(validation)
    with pytest.raises(ValueError, match="Validation count differs"):
        runner.main()
