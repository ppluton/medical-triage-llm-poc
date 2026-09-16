import json

import pytest

from triage_poc.evaluation_reserve import freeze_triage_reserve


def _scenario(identifier, category, language):
    return {
        "id": identifier,
        "synthetic": True,
        "split": "held_out_project_reserve",
        "category": category,
        "reference_status": "proposed_educational_only",
        "expected_level": "moderate",
        "request": {
            "language": language,
            "patient_context": {
                "age_group": "adult",
                "symptoms": [identifier],
                "duration": None,
                "medical_history": [],
                "allergies": [],
                "medications": [],
                "vitals": {},
            },
        },
    }


def _fixture(tmp_path):
    categories = [
        "chest_pain",
        "respiratory_distress",
        "neurological_deficit",
        "pediatric",
        "pregnancy",
        "vulnerability",
        "insufficient_information",
        "contradictory_information",
        "other",
    ]
    rows = []
    for index, category in enumerate(categories):
        rows.append(_scenario(f"reserve-triage-v1-{index}-fr", category, "fr"))
        rows.append(_scenario(f"reserve-triage-v1-{index}-en", category, "en"))
    reserve = tmp_path / "reserve.json"
    reserve.write_text(json.dumps(rows))
    development = tmp_path / "development.json"
    development.write_text(json.dumps([]))
    return reserve, development, rows


def test_freezes_balanced_isolated_reserve(tmp_path):
    reserve, development, _ = _fixture(tmp_path)
    manifest = freeze_triage_reserve(reserve, development)
    assert manifest["status"] == "frozen_not_evaluated"
    assert manifest["counts"]["languages"] == {"en": 9, "fr": 9}
    assert set(manifest["counts"]["categories"].values()) == {2}
    assert manifest["isolation"]["exact_request_digest_overlap"] == 0


def test_rejects_development_overlap_and_non_proposed_reference(tmp_path):
    reserve, development, rows = _fixture(tmp_path)
    development.write_text(json.dumps([{**rows[0], "id": "development-copy"}]))
    with pytest.raises(ValueError, match="overlaps"):
        freeze_triage_reserve(reserve, development)
    development.write_text("[]")
    rows[0]["reference_status"] = "clinically_validated"
    reserve.write_text(json.dumps(rows))
    with pytest.raises(ValueError, match="contract"):
        freeze_triage_reserve(reserve, development)
