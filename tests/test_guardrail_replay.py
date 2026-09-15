import pytest

from triage_poc.guardrail_replay import summarize_guardrail_replay


def _scenario(identifier, category, expected, symptom, age="adult"):
    return {
        "id": identifier,
        "synthetic": True,
        "category": category,
        "expected_level": expected,
        "request": {
            "language": "en",
            "patient_context": {
                "age_group": age,
                "symptoms": [symptom],
                "vitals": {},
            },
        },
    }


def _record(identifier, level, summary):
    return {
        "id": identifier,
        "success": True,
        "response": {
            "triage_level": level,
            "summary": summary,
            "clinical_rationale": [summary],
            "missing_information": [],
            "follow_up_questions": [],
            "red_flags": [],
        },
    }


def test_replay_reports_priority_and_fallback_without_source_text():
    scenarios = [
        _scenario(
            "critical",
            "respiratory_distress",
            "maximum",
            "Severe breathing difficulty, cannot finish a sentence.",
        ),
        _scenario(
            "unknown",
            "insufficient_information",
            "moderate",
            "I do not feel well.",
            age="unknown",
        ),
    ]
    reports = {
        "sft": {
            "records": [
                _record("critical", "moderate", "Supplied symptom."),
                _record("unknown", "deferred", "The patient is stable."),
            ]
        }
    }
    summary = summarize_guardrail_replay(scenarios, reports)
    metrics = summary["models"]["sft"]
    assert metrics["critical_recall_after_replay"] == 1.0
    assert metrics["critical_red_flag_coverage_after_replay"] == 1.0
    assert metrics["uncertainty_priority_floor_rate_after_replay"] == 1.0
    assert metrics["guardrail_status_counts"] == {"corrected": 1, "safe_fallback": 1}
    assert "Severe breathing" not in str(summary)


def test_replay_refuses_incomplete_report_coverage():
    scenarios = [_scenario("one", "other", "deferred", "Mild symptom")]
    with pytest.raises(ValueError, match="coverage mismatch"):
        summarize_guardrail_replay(scenarios, {"base": {"records": []}})
