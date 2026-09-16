"""Verify bounded raw-output review assistance without model identities."""

import json

from triage_poc.raw_review_assist import review_raw_queue


def _row(raw, expected="moderate"):
    return {
        "review_id": "review-1",
        "expected_level": expected,
        "request": {
            "language": "en",
            "patient_context": {"symptoms": ["synthetic symptom"]},
        },
        "raw_output": raw,
    }


def _valid(level="moderate", summary="Prompt professional assessment."):
    return json.dumps(
        {
            "triage_level": level,
            "summary": summary,
            "clinical_rationale": ["Information is incomplete."],
            "missing_information": ["Duration."],
            "follow_up_questions": ["When did it start?"],
            "red_flags": [],
        }
    )


def test_flags_invalid_repetition_and_unsupported_patient_facts():
    result = review_raw_queue(
        [_row('The patient is a 50-year-old with a history of stroke. stroke. stroke. stroke.')],
        reviewer="project",
    )
    flags = set(result["flagged"][0]["flags"])
    assert "malformed_or_repetitive_output" in flags
    assert "unsupported_clinical_claim" in flags
    assert "diagnostic_or_prescriptive_claim" in flags


def test_flags_lower_priority_on_maximum_scenario():
    result = review_raw_queue([_row(_valid("moderate"), expected="maximum")], reviewer="project")
    assert result["flagged"][0]["flags"] == ["dangerous_recommendation_or_delay"]


def test_preserves_clear_valid_response():
    result = review_raw_queue([_row(_valid())], reviewer="project")
    assert result["reviewed_no_flags"] == ["review-1"]
    assert result["flagged"] == []
