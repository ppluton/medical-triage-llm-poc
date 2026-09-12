import json
from pathlib import Path

import pytest

from triage_poc.triage_probe import messages_for_scenario, score_outputs


def test_development_coverage_and_no_reference_leak():
    rows = json.loads(Path("data/samples/synthetic-triage-development-v2.json").read_text())
    assert len(rows) == 18
    assert len({r["id"] for r in rows}) == 18
    assert len({r["category"] for r in rows}) == 9
    for category in {r["category"] for r in rows}:
        assert {r["request"]["language"] for r in rows if r["category"] == category} == {"fr", "en"}
    for row in rows:
        altered = {**row, "expected_level": "never expose this reference"}
        assert messages_for_scenario(row) == messages_for_scenario(altered)
        if row["category"] in {"insufficient_information", "contradictory_information"}:
            assert row["expected_level"] == "moderate"


def test_invalid_json_is_not_silently_removed_from_agreement():
    rows = [
        {"id": str(i), "expected_level": "maximum", "reference_status": "proposed"}
        for i in range(2)
    ]
    valid = json.dumps(
        {
            "triage_level": "maximum",
            "summary": "Synthetic response",
            "clinical_rationale": ["Synthetic reason"],
            "missing_information": [],
        }
    )
    outputs = [{"id": "0", "output": valid}, {"id": "1", "output": "not JSON"}]
    result = score_outputs(rows, outputs)
    assert result["valid_schema"] == 1
    assert result["agreement_on_all_records"] == 0.5
    assert result["valid_only_metrics"]["exact_match_rate"] == 1
    with pytest.raises(ValueError, match="alignment"):
        score_outputs(rows, list(reversed(outputs)))


def test_reload_diagnostic_preserves_difference_and_truncation():
    from triage_poc.triage_probe import compare_reload

    prior = {"record_id": "synthetic-reload", "generated_token_ids": [10, 20, 30]}
    observed = {"generated_token_ids": [10, 21], "output": "Synthetic output"}
    result = compare_reload(prior, observed)
    assert result["identical"] is False
    assert result["first_different_token"] == 1
    assert result["expected_token_ids"] == [10, 20, 30]
    assert result["observed"]["generated_token_ids"] == [10, 21]
    assert result["observed"]["output"] == "Synthetic output"
    assert compare_reload(prior, {"generated_token_ids": [10, 20]})[
        "first_different_token"
    ] == 2
    equal = compare_reload(prior, {"generated_token_ids": [10, 20, 30]})
    assert equal["identical"] is True
    assert equal["first_different_token"] is None
