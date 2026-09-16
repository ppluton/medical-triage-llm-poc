import json

import pytest

from triage_poc.comparison import sha256
from triage_poc.dpo_review import PAYLOAD_FIELDS, finalize_dpo_review


def _row(split: str, suffix: str) -> dict:
    return {
        "record_id": f"row-{suffix}",
        "split": split,
        "language": "en",
        "prompt": f"Prompt {suffix}",
        "chosen": f"Chosen {suffix}",
        "rejected": f"Rejected {suffix}",
        "preference_rationale": "Source biomedical preference; project review pending.",
        "source_label_type": "hard",
        "source": {
            "manifest_id": "source-fixture",
            "license": "MIT",
            "revision": "abc",
            "locator": f"fixture:{suffix}",
        },
        "pii_anonymization_status": "passed_direct_identifiers_only",
        "privacy_review_status": "approved_for_educational_dpo",
        "project_review_status": "approved_for_educational_dpo",
        "clinical_review_status": "not_performed",
    }


def _fixture(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    rows = {"train": [_row("train", "train")], "validation": [_row("validation", "val")]}
    artifacts = {}
    for split, values in rows.items():
        path = source / f"{split}.jsonl"
        path.write_text("".join(json.dumps(row) + "\n" for row in values))
        artifacts[split] = {"records": len(values), "sha256": sha256(path)}
    parent = {
        "status": "approved_for_educational_dpo",
        "clinical_review_status": "not_performed",
        "artifacts": artifacts,
        "protected_prompt_hashes": [],
        "source_manifest_id": "source-fixture",
        "source_revision": "abc",
        "source_sha256": "a" * 64,
        "language": "en",
    }
    parent_path = source / "manifest.json"
    parent_path.write_text(json.dumps(parent))
    sft = tmp_path / "sft.json"
    canonical = tmp_path / "sft.jsonl"
    canonical.write_text("".join(json.dumps({
        "record_id": f"sft-{index}", "instruction": f"SFT prompt {index}"
    }) + "\n" for index in range(2)))
    sft.write_text(json.dumps({
        "record_count": 2,
        "artifacts": {"canonical": {"sha256": sha256(canonical)}},
    }))
    decision = tmp_path / "decision.json"
    decision.write_text(json.dumps({
        "status": "approved_for_educational_dpo",
        "clinical_validation": "not_performed",
        "reviewer": "fixture project review",
        "dataset_manifest_sha256": sha256(parent_path),
        "sft_manifest_sha256": sha256(sft),
        "sft_canonical_sha256": sha256(canonical),
    }))
    return source, rows, sft, canonical, decision


def test_finalize_dpo_review_changes_only_governance_metadata(tmp_path):
    source, rows, sft, canonical, decision = _fixture(tmp_path)
    output = tmp_path / "output"
    manifest = finalize_dpo_review(
        source,
        output,
        sft_manifest_path=sft,
        sft_canonical_path=canonical,
        decision_path=decision,
        decision_id="ADR-014",
        review_date="2026-09-12",
        manifest_id="fixture-dpo-v2",
    )
    assert manifest["sft_protected_records"] == 2
    assert manifest["clinical_review_status"] == "not_performed"
    assert manifest["current_sft_prompt_hashes"] == 2
    assert len(manifest["protected_prompt_hashes"]) == 2
    for split in ("train", "validation"):
        updated = json.loads((output / f"{split}.jsonl").read_text())
        assert {field: updated.get(field) for field in PAYLOAD_FIELDS} == {
            field: rows[split][0].get(field) for field in PAYLOAD_FIELDS
        }
        assert "project review pending" not in updated["preference_rationale"]
        assert "no healthcare-professional validation" in updated["preference_rationale"]


def test_finalize_dpo_review_refuses_unreviewed_or_mismatched_inputs(tmp_path):
    source, _, sft, canonical, decision = _fixture(tmp_path)
    train = json.loads((source / "train.jsonl").read_text())
    train["privacy_review_status"] = "pending"
    (source / "train.jsonl").write_text(json.dumps(train) + "\n")
    parent_path = source / "manifest.json"
    parent = json.loads(parent_path.read_text())
    parent["artifacts"]["train"]["sha256"] = sha256(source / "train.jsonl")
    parent_path.write_text(json.dumps(parent))
    review = json.loads(decision.read_text())
    review["dataset_manifest_sha256"] = sha256(parent_path)
    review["sft_manifest_sha256"] = sha256(sft)
    decision.write_text(json.dumps(review))
    with pytest.raises(ValueError, match="privacy review"):
        finalize_dpo_review(
            source,
            tmp_path / "output",
            sft_manifest_path=sft,
            sft_canonical_path=canonical,
            decision_path=decision,
            decision_id="ADR-014",
            review_date="2026-09-12",
            manifest_id="fixture-dpo-v2",
        )

    decision.write_text(json.dumps({**review, "dataset_manifest_sha256": "0" * 64}))
    with pytest.raises(ValueError, match="does not match"):
        finalize_dpo_review(
            source,
            tmp_path / "other-output",
            sft_manifest_path=sft,
            sft_canonical_path=canonical,
            decision_path=decision,
            decision_id="ADR-014",
            review_date="2026-09-12",
            manifest_id="fixture-dpo-v2",
        )


def test_finalize_dpo_review_rejects_changed_sft_canonical(tmp_path):
    source, _, sft, canonical, decision = _fixture(tmp_path)
    canonical.write_text(json.dumps({"record_id": "changed", "instruction": "changed"}) + "\n")
    with pytest.raises(ValueError, match="canonical checksum"):
        finalize_dpo_review(
            source,
            tmp_path / "output",
            sft_manifest_path=sft,
            sft_canonical_path=canonical,
            decision_path=decision,
            decision_id="ADR-014",
            review_date="2026-09-12",
            manifest_id="fixture-dpo-v2",
        )
