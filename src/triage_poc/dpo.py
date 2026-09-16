"""Fail-closed DPO handoff: provenance, split isolation, and comparison evidence."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from triage_poc.comparison import sha256
from triage_poc.ultramedical_audit import normalize_text


def prompt_hash(prompt: str) -> str:
    return hashlib.sha256(normalize_text(prompt).encode()).hexdigest()


def validate_preferences(
    train: list[dict], validation: list[dict], protected: set[str], *, require_review: bool = True
) -> None:
    seen = set(protected)
    ids = set()
    for split, rows in [("validation", validation), ("train", train)]:
        if not rows:
            raise ValueError(f"Empty {split} split.")
        for row in rows:
            if row.get("split") != split or row.get("record_id") in ids:
                raise ValueError("Wrong split or duplicate record ID.")
            if not isinstance(row.get("record_id"), str):
                raise ValueError("Missing record ID.")
            ids.add(row["record_id"])
            for field in ("prompt", "chosen", "rejected", "preference_rationale"):
                if not isinstance(row.get(field), str) or not row[field].strip():
                    raise ValueError(f"Missing {field}.")
            if normalize_text(row["chosen"]) == normalize_text(row["rejected"]):
                raise ValueError("Chosen and rejected responses are identical.")
            digest = prompt_hash(row["prompt"])
            if digest in seen:
                raise ValueError("Prompt leakage or duplicate prompt.")
            seen.add(digest)
            if row.get("pii_anonymization_status") not in {
                "passed", "passed_direct_identifiers_only"
            }:
                raise ValueError("PII check not passed.")
            if (require_review and row.get("pii_anonymization_status")
                    == "passed_direct_identifiers_only"
                    and row.get("privacy_review_status") != "approved_for_educational_dpo"):
                raise ValueError("Direct identifier scan requires additional privacy review.")
            source = row.get("source", {})
            if not all(source.get(k) for k in ("manifest_id", "license", "revision", "locator")):
                raise ValueError("Incomplete source provenance.")
            if row.get("clinical_review_status") not in {"not_performed", "approved"}:
                raise ValueError("Explicit clinical review status required.")


def load_sft_identity(manifest_path: Path, adapter: Path) -> dict:
    """Verify the selected weights and tokenizer before loading a model."""
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("schema_version") != "sft-handoff-v1":
        raise ValueError("Unsupported SFT handoff schema.")
    if (not manifest.get("base_model")
            or not re.fullmatch(r"[0-9a-f]{40}", manifest.get("base_revision", ""))):
        raise ValueError("Pinned SFT base identity required.")
    files = manifest.get("files", {})
    required = {"adapter_model.safetensors", "adapter_config.json", "tokenizer.json",
                "tokenizer_config.json", "chat_template.jinja"}
    if not required <= files.keys():
        raise ValueError("SFT weights and tokenizer hashes are required.")
    for name, digest in files.items():
        if Path(name).name != name or not isinstance(digest, str) or len(digest) != 64:
            raise ValueError("Invalid SFT artifact entry.")
        if not (adapter / name).is_file() or sha256(adapter / name) != digest:
            raise ValueError(f"SFT artifact checksum mismatch: {name}")
    config = json.loads((adapter / "adapter_config.json").read_text())
    if config.get("base_model_name_or_path") != manifest["base_model"]:
        raise ValueError("Adapter base differs from the selected SFT base.")
    return manifest


def load_dpo_handoff(directory: Path, comparison: Path, decision: Path,
                     *, sft_sha256: str):
    if not re.fullmatch(r"[0-9a-f]{64}", sft_sha256):
        raise ValueError("Explicit SFT checksum required.")
    summary = json.loads(comparison.read_text())
    review = json.loads(decision.read_text())
    if (summary.get("status") != "completed" or summary.get("test_records_used") != 0
            or summary.get("sft_sha256") != sft_sha256
            or not {"base", "sft"} <= set(summary.get("comparison", {}))):
        raise ValueError("A completed matching Base/SFT validation comparison is required.")
    if (review.get("comparison_sha256") != sha256(comparison)
            or review.get("decision") != "accepted_for_educational_dpo"
            or not review.get("reviewer") or not review.get("rationale")):
        raise ValueError("The actual comparison must be reviewed before DPO.")
    manifest = json.loads((directory / "manifest.json").read_text())
    if manifest.get("status") != "approved_for_educational_dpo":
        raise ValueError("Preference candidate dataset is not yet approved for educational DPO.")
    loaded = {}
    for split in ("train", "validation"):
        path = directory / f"{split}.jsonl"
        if sha256(path) != manifest["artifacts"][split]["sha256"]:
            raise ValueError("DPO artifact checksum mismatch.")
        loaded[split] = [json.loads(line) for line in path.read_text().splitlines()]
        if len(loaded[split]) != manifest["artifacts"][split]["records"]:
            raise ValueError("DPO record count mismatch.")
    validate_preferences(loaded["train"], loaded["validation"],
                         set(manifest["protected_prompt_hashes"]))
    return manifest, loaded


def adapter_fingerprint(model, adapter: str) -> dict:
    """Hash actual finite LoRA tensors, normalizing the adapter name for comparison."""
    import torch

    tensors = {}
    for name, parameter in model.named_parameters():
        if "lora_" not in name or f".{adapter}." not in name:
            continue
        value = parameter.detach().cpu().contiguous()
        if not torch.isfinite(value).all():
            raise ValueError(f"Non-finite adapter tensor: {name}")
        key = name.replace(f".{adapter}.", ".adapter.")
        tensors[key] = {
            "shape": list(value.shape), "dtype": str(value.dtype),
            "sha256": hashlib.sha256(value.view(torch.uint8).numpy().tobytes()).hexdigest(),
        }
    if not tensors:
        raise ValueError(f"No LoRA tensors found for adapter: {adapter}")
    return tensors


def verify_dpo_weight_changes(before: dict, after: dict) -> dict:
    """Fail rather than claim completed DPO with a changed reference or unchanged policy."""
    if before["policy"] != before["reference"]:
        raise ValueError("Policy and reference must start from identical SFT tensors")
    if before["reference"] != after["reference"]:
        raise ValueError("DPO reference weights changed")
    if before["policy"].keys() != after["policy"].keys():
        raise ValueError("DPO policy tensor inventory changed")
    changed = sum(before["policy"][key] != after["policy"][key] for key in before["policy"])
    if not changed:
        raise ValueError("DPO policy weights did not change")
    return {"reference_unchanged": True, "policy_changed_tensors": changed,
            "policy_total_tensors": len(before["policy"])}


def saved_adapter_fingerprint(path: Path) -> dict:
    """Read saved LoRA tensors in the same namespace as the runtime fingerprint."""
    import torch
    from safetensors.torch import load_file

    tensors = {}
    for name, value in load_file(str(path), device="cpu").items():
        key = re.sub(r"(\.lora_[AB])\.weight$", r"\1.adapter.weight", name)
        if key == name or not torch.isfinite(value).all():
            raise ValueError("Unexpected or non-finite saved LoRA tensor")
        value = value.contiguous()
        tensors[key] = {
            "shape": list(value.shape), "dtype": str(value.dtype),
            "sha256": hashlib.sha256(value.view(torch.uint8).numpy().tobytes()).hexdigest(),
        }
    if not tensors:
        raise ValueError("Empty saved adapter")
    return tensors


def verify_completed_dpo(directory: Path, sft_manifest: Path, sft_adapter: Path) -> dict:
    """Bind the saved policy to its actual training tensors and selected SFT reference."""
    identity = load_sft_identity(sft_manifest, sft_adapter)
    summary = json.loads((directory / "run_summary.json").read_text())
    checks = json.loads((directory / "weight_checks.json").read_text())
    if (summary.get("status") != "completed_educational_dpo"
            or summary.get("test_records_used") != 0
            or summary.get("sft_manifest_sha256") != sha256(sft_manifest)
            or summary.get("sft_sha256") != identity["files"]["adapter_model.safetensors"]
            or summary.get("base_model") != identity["base_model"]
            or summary.get("base_revision") != identity["base_revision"]):
        raise ValueError("DPO summary does not match the selected SFT experiment")
    measured = verify_dpo_weight_changes(checks["before"], checks["after"])
    if measured != checks["checks"] or measured != summary.get("weight_checks"):
        raise ValueError("DPO declared weight checks disagree with actual fingerprints")
    if saved_adapter_fingerprint(sft_adapter / "adapter_model.safetensors") != checks["before"][
        "reference"
    ]:
        raise ValueError("DPO reference fingerprints differ from the actual SFT file")
    adapter = directory / "adapter/policy"
    saved_policy = saved_adapter_fingerprint(adapter / "adapter_model.safetensors")
    if saved_policy != checks["after"]["policy"]:
        raise ValueError("Saved DPO adapter differs from the final policy tensors")
    for name in ("tokenizer.json", "chat_template.jinja"):
        if sha256(adapter / name) != identity["files"][name]:
            raise ValueError("DPO tokenizer vocabulary or template differs from SFT")
    config = json.loads((adapter / "adapter_config.json").read_text())
    if config.get("base_model_name_or_path") != identity["base_model"]:
        raise ValueError("Saved DPO adapter has a different base model")
    return {"status": "saved_weights_verified", "weight_checks": measured,
            "adapter_sha256": sha256(adapter / "adapter_model.safetensors"),
            "run_summary_sha256": sha256(directory / "run_summary.json"),
            "limits": ["Exact saved weights do not prove inference reload or quality."]}
