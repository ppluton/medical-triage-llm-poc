"""Finalize educational DPO review metadata without changing training payloads."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from triage_poc.comparison import sha256
from triage_poc.dpo import prompt_hash, validate_preferences

PAYLOAD_FIELDS = (
    "record_id",
    "split",
    "language",
    "prompt",
    "chosen",
    "rejected",
    "source_label_type",
    "source",
)


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))


def _finalize_row(row: dict, *, decision_id: str, review_date: str) -> dict:
    if row.get("project_review_status") != "approved_for_educational_dpo":
        raise ValueError("Only an already approved educational DPO row can be finalized.")
    if row.get("privacy_review_status") != "approved_for_educational_dpo":
        raise ValueError("A finalized row requires the documented project privacy review.")
    if row.get("clinical_review_status") != "not_performed":
        raise ValueError("This workflow must not claim healthcare-professional review.")
    label_type = row.get("source_label_type")
    if not isinstance(label_type, str) or not label_type:
        raise ValueError("Source preference label type is required.")

    finalized = deepcopy(row)
    finalized["preference_rationale"] = (
        f"UltraMedical source preference (label_type={label_type}); admitted by the "
        "documented project review for educational DPO only; no healthcare-professional "
        "validation."
    )
    finalized["project_review_decision_id"] = decision_id
    finalized["project_review_date"] = review_date
    return finalized


def finalize_dpo_review(
    source_directory: Path,
    output_directory: Path,
    *,
    sft_manifest_path: Path,
    sft_canonical_path: Path,
    decision_path: Path,
    decision_id: str,
    review_date: str,
    manifest_id: str,
) -> dict:
    """Write a fresh, lineage-bound DPO version with corrected review metadata."""
    if output_directory.exists():
        raise ValueError("Choose a fresh output directory.")

    parent_manifest_path = source_directory / "manifest.json"
    parent_manifest = json.loads(parent_manifest_path.read_text())
    if parent_manifest.get("status") != "approved_for_educational_dpo":
        raise ValueError("Parent DPO dataset is not approved for educational use.")

    sft_manifest = json.loads(sft_manifest_path.read_text())
    sft_records = sft_manifest.get("record_count")
    canonical = sft_manifest.get("artifacts", {}).get("canonical", {})
    if not isinstance(sft_records, int) or sft_records < 1 or not canonical.get("sha256"):
        raise ValueError("SFT manifest does not expose its canonical protected dataset.")
    if sha256(sft_canonical_path) != canonical["sha256"]:
        raise ValueError("SFT canonical checksum does not match its manifest.")
    sft_rows = _read_jsonl(sft_canonical_path)
    if len(sft_rows) != sft_records:
        raise ValueError("SFT canonical record count does not match its manifest.")
    current_sft_prompt_hashes = set()
    current_sft_ids = set()
    for row in sft_rows:
        if not isinstance(row.get("record_id"), str) or row["record_id"] in current_sft_ids:
            raise ValueError("SFT canonical record IDs must be present and unique.")
        if not isinstance(row.get("instruction"), str) or not row["instruction"].strip():
            raise ValueError("SFT canonical instruction is required.")
        current_sft_ids.add(row["record_id"])
        current_sft_prompt_hashes.add(prompt_hash(row["instruction"]))
    if len(current_sft_prompt_hashes) != sft_records:
        raise ValueError("SFT canonical instructions must be unique after normalization.")

    decision = json.loads(decision_path.read_text())
    if (
        decision.get("status") != "approved_for_educational_dpo"
        or decision.get("clinical_validation") != "not_performed"
        or not decision.get("reviewer")
    ):
        raise ValueError("The project review decision is incomplete.")
    if decision.get("dataset_manifest_sha256") != sha256(parent_manifest_path):
        raise ValueError("Project review decision does not match the parent DPO manifest.")
    if (
        decision.get("sft_manifest_sha256") != sha256(sft_manifest_path)
        or decision.get("sft_canonical_sha256") != canonical["sha256"]
    ):
        raise ValueError("Project review decision does not match the protected SFT corpus.")

    protected = set(parent_manifest.get("protected_prompt_hashes", []))
    protected.update(current_sft_prompt_hashes)
    finalized: dict[str, list[dict]] = {}
    input_artifacts = {}
    output_directory.mkdir(parents=True)
    for split in ("train", "validation"):
        source_path = source_directory / f"{split}.jsonl"
        artifact = parent_manifest.get("artifacts", {}).get(split, {})
        if sha256(source_path) != artifact.get("sha256"):
            raise ValueError(f"Parent {split} checksum mismatch.")
        rows = _read_jsonl(source_path)
        if len(rows) != artifact.get("records"):
            raise ValueError(f"Parent {split} record count mismatch.")
        updated = [
            _finalize_row(row, decision_id=decision_id, review_date=review_date) for row in rows
        ]
        for before, after in zip(rows, updated, strict=True):
            if {field: before.get(field) for field in PAYLOAD_FIELDS} != {
                field: after.get(field) for field in PAYLOAD_FIELDS
            }:
                raise AssertionError("DPO training payload or source lineage changed.")
        finalized[split] = updated
        input_artifacts[split] = {
            "records": len(rows),
            "sha256": sha256(source_path),
        }

    validate_preferences(finalized["train"], finalized["validation"], protected)

    artifacts = {}
    for split, rows in finalized.items():
        path = output_directory / f"{split}.jsonl"
        _write_jsonl(path, rows)
        artifacts[split] = {"records": len(rows), "sha256": sha256(path)}

    manifest = {
        "manifest_id": manifest_id,
        "schema_version": "1.0.0",
        "status": "approved_for_educational_dpo",
        "clinical_review_status": "not_performed",
        "project_review_decision_id": decision_id,
        "project_review_date": review_date,
        "project_review_reviewer": decision["reviewer"],
        "artifacts": artifacts,
        "parent_artifacts": input_artifacts,
        "parent_manifest_sha256": sha256(parent_manifest_path),
        "decision_sha256": sha256(decision_path),
        "source_manifest_id": parent_manifest["source_manifest_id"],
        "source_revision": parent_manifest["source_revision"],
        "source_sha256": parent_manifest["source_sha256"],
        "sft_manifest_sha256": sha256(sft_manifest_path),
        "sft_protected_records": sft_records,
        "protected_sft_canonical_sha256": canonical["sha256"],
        "current_sft_prompt_hashes": len(current_sft_prompt_hashes),
        "protected_prompt_hashes": sorted(protected),
        "test_answers_used": 0,
        "language": parent_manifest["language"],
        "payload_fields_unchanged": list(PAYLOAD_FIELDS),
        "governance_changes": [
            "replace stale pending preference rationale with the exact project-review scope",
            "bind each row to the documented review decision and date",
            "bind the manifest to the current protected SFT manifest",
            "extend prompt protection with every current SFT canonical instruction",
        ],
        "limits": [
            "Source biomedical preferences are not validated triage preferences.",
            "No healthcare professional reviewed or approved this dataset.",
            "The dataset is English-only and does not establish French preference alignment.",
            "The privacy decision is limited to this documented educational POC.",
        ],
    }
    (output_directory / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    )
    return manifest
