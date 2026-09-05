"""Fail-closed DPO handoff: provenance, split isolation, and comparison evidence."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from triage_poc.comparison import SFT_SHA256, sha256
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


def load_dpo_handoff(directory: Path, comparison: Path, decision: Path):
    summary = json.loads(comparison.read_text())
    review = json.loads(decision.read_text())
    if (summary.get("status") != "completed" or summary.get("test_records_used") != 0
            or summary.get("sft_sha256") != SFT_SHA256
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
