"""Build a fail-closed SFT identity after a read-only fresh-process reload."""

from __future__ import annotations

import json
from pathlib import Path

from triage_poc.comparison import sha256
from triage_poc.sft_pilot import require_complete_checkpoint

HANDOFF_FILES = (
    "adapter_model.safetensors",
    "adapter_config.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "chat_template.jinja",
)


def build_sft_handoff(
    run_directory: Path,
    reload_directory: Path,
    config_path: Path,
    dataset_manifest_path: Path,
    output_path: Path,
    *,
    checkpoint_label: str,
) -> dict:
    """Bind exact saved weights to their config, data, tokenizer, and reload proof."""

    if output_path.exists():
        raise ValueError("Choose a fresh SFT handoff output path.")
    config = json.loads(config_path.read_text())
    summary = json.loads((run_directory / "summary.json").read_text())
    reload = json.loads((reload_directory / "summary.json").read_text())
    if (
        summary.get("status") != "pilot_completed_pending_quality_review"
        or summary.get("mode") != "pilot"
        or summary.get("configuration") != config
        or summary.get("test_records_used") != 0
        or summary.get("steps") != config.get("pilot_stop_after_steps")
    ):
        raise ValueError("SFT pilot summary does not match the frozen configuration.")
    checkpoint = run_directory / "trainer" / f"checkpoint-{summary['steps']}"
    hashes = require_complete_checkpoint(checkpoint, summary["steps"])
    if hashes != summary.get("checkpoint_hashes"):
        raise ValueError("SFT checkpoint hashes differ from the completed run summary.")
    if (
        reload.get("status") != "pilot_fresh_reload_verified"
        or reload.get("optimizer_steps_executed") != 0
        or reload.get("test_records_used") != 0
        or reload.get("configuration") != config
        or reload.get("checkpoint_hashes") != hashes
        or reload.get("identical_generations") != len(config["evaluation"]["generation_record_ids"])
        or reload.get("absolute_loss_delta", 1) > 1e-5
    ):
        raise ValueError("Fresh-process reload proof does not match the selected SFT checkpoint.")
    dataset_manifest = json.loads(dataset_manifest_path.read_text())
    if dataset_manifest.get("artifacts", {}).get("canonical", {}).get("sha256") != config.get(
        "dataset_sha256"
    ):
        raise ValueError("SFT dataset manifest differs from the training configuration.")
    files = {}
    for name in HANDOFF_FILES:
        path = checkpoint / name
        if not path.is_file() or not path.stat().st_size:
            raise ValueError(f"Missing SFT handoff file: {name}")
        files[name] = sha256(path)
    adapter = json.loads((checkpoint / "adapter_config.json").read_text())
    if adapter.get("base_model_name_or_path") != config.get("base_model"):
        raise ValueError("Saved adapter base differs from the frozen SFT configuration.")
    if files["chat_template.jinja"] != config.get("training_chat_template_sha256"):
        raise ValueError("Saved chat template differs from the training template.")
    handoff = {
        "schema_version": "sft-handoff-v1",
        "date": config["date"],
        "status": "verified_artifacts_not_clinical_approval",
        "checkpoint": checkpoint_label,
        "base_model": config["base_model"],
        "base_revision": config["base_revision"],
        "files": files,
        "source_run_sha256": sha256(run_directory / "summary.json"),
        "reload_summary_sha256": sha256(reload_directory / "summary.json"),
        "dataset_manifest_sha256": sha256(dataset_manifest_path),
        "dataset_sha256": config["dataset_sha256"],
        "test_records_used": 0,
        "clinical_validation": "not_performed",
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(handoff, indent=2) + "\n")
    return handoff
