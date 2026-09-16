"""Test the one-shot reserve gates without reading the real held-out scenarios."""

import json

import pytest

from triage_poc.evaluation_reserve import sha256
from triage_poc.final_reserve import validate_model_selection


def _files(tmp_path):
    comparison = tmp_path / "summary.json"
    comparison.write_text(
        json.dumps(
            {
                "status": "completed",
                "optimizer_steps": 0,
                "test_records_used": 0,
                "evaluation_split": "validation",
            }
        )
    )
    decision = tmp_path / "selection.json"
    decision.write_text(
        json.dumps(
            {
                "status": "selected_for_one_shot_reserve",
                "selected_variant": "sft",
                "comparison_summary_sha256": sha256(comparison),
                "rationale": "DPO did not demonstrate a development-set benefit.",
                "held_out_reserve_used": False,
            }
        )
    )
    return decision, comparison


def test_accepts_selection_bound_to_development_comparison(tmp_path):
    decision, comparison = _files(tmp_path)
    assert validate_model_selection(decision, comparison)["selected_variant"] == "sft"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("selected_variant", "base"),
        ("held_out_reserve_used", True),
        ("rationale", ""),
        ("comparison_summary_sha256", "0" * 64),
    ],
)
def test_rejects_unfrozen_or_post_reserve_selection(tmp_path, field, value):
    decision, comparison = _files(tmp_path)
    payload = json.loads(decision.read_text())
    payload[field] = value
    decision.write_text(json.dumps(payload))
    with pytest.raises(ValueError):
        validate_model_selection(decision, comparison)


def test_rejects_comparison_that_used_test_data(tmp_path):
    decision, comparison = _files(tmp_path)
    payload = json.loads(comparison.read_text())
    payload["test_records_used"] = 1
    comparison.write_text(json.dumps(payload))
    selection = json.loads(decision.read_text())
    selection["comparison_summary_sha256"] = sha256(comparison)
    decision.write_text(json.dumps(selection))
    with pytest.raises(ValueError):
        validate_model_selection(decision, comparison)
