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
