import json

import pytest

from triage_poc.comparison import SFT_SHA256, sha256
from triage_poc.dpo import load_dpo_handoff, load_sft_identity, prompt_hash, validate_preferences


def preference(split, prompt):
    return {"record_id": prompt, "split": split, "prompt": prompt,
            "chosen": "Synthetic preferred response.", "rejected": "Synthetic rejected response.",
            "preference_rationale": "Source-provided preference, not clinical approval.",
            "source": {"manifest_id": "fixture", "license": "MIT", "revision": "abc",
                       "locator": "synthetic:0"}, "pii_anonymization_status": "passed",
            "clinical_review_status": "not_performed"}


def test_dpo_rejects_leakage_after_normalization_and_unreviewed_pii():
    train, validation = [preference("train", "A")], [preference("validation", "B")]
    validate_preferences(train, validation, set())
    with pytest.raises(ValueError, match="leakage"):
        validate_preferences(train, validation, {prompt_hash("A!")})
    train[0]["prompt"] = "B!"
    with pytest.raises(ValueError, match="leakage"):
        validate_preferences(train, validation, set())
    train[0]["prompt"] = "A"
    train[0]["pii_anonymization_status"] = "manual_review_required"
    with pytest.raises(ValueError, match="PII"):
        validate_preferences(train, validation, set())


def test_dpo_refuses_missing_comparison_and_unapproved_candidates(tmp_path):
    summary, decision = tmp_path / "summary.json", tmp_path / "decision.json"
    summary.write_text(json.dumps({"status": "completed", "sft_sha256": SFT_SHA256,
                                  "test_records_used": 0, "comparison": {"base": {}, "sft": {}}}))
    decision.write_text('{}')
    with pytest.raises(ValueError, match="reviewed"):
        load_dpo_handoff(tmp_path, summary, decision, sft_sha256=SFT_SHA256)
    decision.write_text(json.dumps({"comparison_sha256": sha256(summary),
                                   "decision": "accepted_for_educational_dpo",
                                   "reviewer": "synthetic-test", "rationale": "fixture"}))
    (tmp_path / "manifest.json").write_text('{"status":"candidate"}')
    with pytest.raises(ValueError, match="not yet approved"):
        load_dpo_handoff(tmp_path, summary, decision, sft_sha256=SFT_SHA256)
    value = json.loads(summary.read_text())
    value['test_records_used'] = 1
    summary.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="matching"):
        load_dpo_handoff(tmp_path, summary, decision, sft_sha256=SFT_SHA256)


def test_direct_identifier_only_scan_cannot_be_promoted_without_privacy_review():
    train = [preference("train", "A")]
    validation = [preference("validation", "B")]
    train[0]["pii_anonymization_status"] = "passed_direct_identifiers_only"
    validate_preferences(train, validation, set(), require_review=False)
    with pytest.raises(ValueError, match="privacy review"):
        validate_preferences(train, validation, set())


def test_sft_identity_rejects_changed_tokenizer_and_weights(tmp_path):
    names = ["adapter_model.safetensors", "adapter_config.json", "tokenizer.json",
             "tokenizer_config.json", "chat_template.jinja"]
    for name in names:
        (tmp_path / name).write_text('{"base_model_name_or_path":"synthetic/base"}')
    identity = {"schema_version": "sft-handoff-v1", "base_model": "synthetic/base",
                "base_revision": "a" * 40,
                "files": {name: sha256(tmp_path / name) for name in names}}
    manifest = tmp_path / "identity.json"
    manifest.write_text(json.dumps(identity))
    assert load_sft_identity(manifest, tmp_path) == identity
    for name in ["tokenizer.json", "chat_template.jinja", "adapter_model.safetensors"]:
        original = (tmp_path / name).read_text()
        (tmp_path / name).write_text("different artifact")
        with pytest.raises(ValueError, match="checksum mismatch"):
            load_sft_identity(manifest, tmp_path)
        (tmp_path / name).write_text(original)
    identity["base_model"] = "wrong/base"
    manifest.write_text(json.dumps(identity))
    with pytest.raises(ValueError, match="base differs"):
        load_sft_identity(manifest, tmp_path)


def test_new_sft_handoff_succeeds_and_rejects_old_comparison(tmp_path):
    selected = "a" * 64
    summary, decision = tmp_path / "summary.json", tmp_path / "decision.json"
    summary.write_text(json.dumps({"status": "completed", "sft_sha256": selected,
                                  "test_records_used": 0, "comparison": {"base": {}, "sft": {}}}))
    decision.write_text(json.dumps({"comparison_sha256": sha256(summary),
                                   "decision": "accepted_for_educational_dpo",
                                   "reviewer": "synthetic-test", "rationale": "fixture"}))
    artifacts = {}
    for split in ("train", "validation"):
        path = tmp_path / f"{split}.jsonl"
        path.write_text(json.dumps(preference(split, split)) + "\n")
        artifacts[split] = {"sha256": sha256(path), "records": 1}
    (tmp_path / "manifest.json").write_text(json.dumps({
        "status": "approved_for_educational_dpo", "artifacts": artifacts,
        "protected_prompt_hashes": []}))
    _, loaded = load_dpo_handoff(tmp_path, summary, decision, sft_sha256=selected)
    assert len(loaded["train"]) == 1
    with pytest.raises(ValueError, match="matching"):
        load_dpo_handoff(tmp_path, summary, decision, sft_sha256=SFT_SHA256)


def test_real_tensor_fingerprints_detect_reference_mutation_and_unchanged_policy():
    import torch

    from triage_poc.dpo import adapter_fingerprint, verify_dpo_weight_changes

    model = torch.nn.Module()
    model.lora_A = torch.nn.ModuleDict({
        name: torch.nn.Linear(3, 2, bias=False) for name in ("policy", "reference")
    })
    with torch.no_grad():
        for layer in model.lora_A.values():
            layer.weight.fill_(1)
    def snapshot():
        return {name: adapter_fingerprint(model, name) for name in ("policy", "reference")}

    before = snapshot()
    with pytest.raises(ValueError, match="did not change"):
        verify_dpo_weight_changes(before, snapshot())
    with torch.no_grad():
        model.lora_A["policy"].weight.add_(0.25)
    assert verify_dpo_weight_changes(before, snapshot())["policy_changed_tensors"] == 1
    with torch.no_grad():
        model.lora_A["reference"].weight.add_(0.25)
    with pytest.raises(ValueError, match="reference weights changed"):
        verify_dpo_weight_changes(before, snapshot())
    with torch.no_grad():
        model.lora_A["policy"].weight.fill_(float("nan"))
    with pytest.raises(ValueError, match="Non-finite"):
        adapter_fingerprint(model, "policy")
    with pytest.raises(ValueError, match="No LoRA"):
        adapter_fingerprint(model, "missing")


def test_saved_adapter_fingerprint_matches_runtime_and_detects_alteration(tmp_path):
    import torch
    from safetensors.torch import save_file

    from triage_poc.dpo import adapter_fingerprint, saved_adapter_fingerprint

    model = torch.nn.Module()
    model.layer = torch.nn.Module()
    model.layer.lora_A = torch.nn.ModuleDict({"policy": torch.nn.Linear(3, 2, bias=False)})
    value = model.layer.lora_A["policy"].weight.detach().clone()
    path = tmp_path / "adapter.safetensors"
    save_file({"layer.lora_A.weight": value}, str(path))
    assert saved_adapter_fingerprint(path) == adapter_fingerprint(model, "policy")
    save_file({"layer.lora_A.weight": value + 1}, str(path))
    assert saved_adapter_fingerprint(path) != adapter_fingerprint(model, "policy")
    save_file({"layer.lora_A.weight": torch.full_like(value, float("nan"))}, str(path))
    with pytest.raises(ValueError, match="non-finite"):
        saved_adapter_fingerprint(path)


def test_completed_dpo_is_bound_to_saved_policy_and_selected_reference(tmp_path):
    import torch
    from safetensors.torch import save_file

    from triage_poc.dpo import (
        saved_adapter_fingerprint,
        verify_completed_dpo,
        verify_dpo_weight_changes,
    )

    sft = tmp_path / "sft"
    adapter = tmp_path / "run/adapter/policy"
    sft.mkdir()
    adapter.mkdir(parents=True)
    for directory, value in ((sft, 1.0), (adapter, 2.0)):
        save_file({"layer.lora_A.weight": torch.full((2, 3), value)},
                  str(directory / "adapter_model.safetensors"))
        for name in ("tokenizer.json", "tokenizer_config.json", "chat_template.jinja"):
            (directory / name).write_text("synthetic fixture")
        (directory / "adapter_config.json").write_text(json.dumps({
            "base_model_name_or_path": "synthetic/base"}))
    identity = {"schema_version": "sft-handoff-v1", "base_model": "synthetic/base",
                "base_revision": "a" * 40,
                "files": {p.name: sha256(p) for p in sft.iterdir()}}
    manifest = tmp_path / "identity.json"
    manifest.write_text(json.dumps(identity))
    before = saved_adapter_fingerprint(sft / "adapter_model.safetensors")
    after = saved_adapter_fingerprint(adapter / "adapter_model.safetensors")
    snapshots = {"before": {"policy": before, "reference": before},
                 "after": {"policy": after, "reference": before}}
    measured = verify_dpo_weight_changes(snapshots["before"], snapshots["after"])
    run = tmp_path / "run"
    (run / "weight_checks.json").write_text(json.dumps({**snapshots, "checks": measured}))
    summary = {"status": "completed_educational_dpo", "test_records_used": 0,
               "sft_manifest_sha256": sha256(manifest),
               "sft_sha256": identity["files"]["adapter_model.safetensors"],
               "base_model": identity["base_model"], "base_revision": identity["base_revision"],
               "weight_checks": measured}
    (run / "run_summary.json").write_text(json.dumps(summary))
    assert verify_completed_dpo(run, manifest, sft)["status"] == "saved_weights_verified"
    save_file({"layer.lora_A.weight": torch.full((2, 3), 3.0)},
              str(adapter / "adapter_model.safetensors"))
    with pytest.raises(ValueError, match="final policy"):
        verify_completed_dpo(run, manifest, sft)
    summary["sft_sha256"] = "b" * 64
    (run / "run_summary.json").write_text(json.dumps(summary))
    with pytest.raises(ValueError, match="selected SFT"):
        verify_completed_dpo(run, manifest, sft)
