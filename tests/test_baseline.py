import pytest

from triage_poc.baseline import (
    build_baseline_messages,
    extract_first_json_object,
    parse_triage_output,
    summarize_baseline_results,
)


def test_prompt_does_not_leak_expected_level():
    scenario = {
        "language": "fr",
        "context": "Contexte synthétique.",
        "expected_level": "maximum",
    }

    messages = build_baseline_messages(scenario)

    assert "Contexte synthétique" in messages[1]["content"]
    assert '"maximum|moderate|deferred"' in messages[1]["content"]
    assert "expected_level" not in messages[1]["content"]


def test_extracts_json_after_optional_model_preamble():
    parsed = extract_first_json_object(
        'draft\n{"triage_level":"moderate","summary":"Brace } in text",'
        '"missing_information":[],"safety_notice":"notice"}\ntrailing'
    )

    assert parsed["triage_level"] == "moderate"
    assert parsed["summary"] == "Brace } in text"


def test_rejects_invalid_or_incomplete_output_contract():
    with pytest.raises(ValueError, match="No JSON"):
        parse_triage_output("not json")
    with pytest.raises(ValueError, match="triage_level"):
        parse_triage_output(
            '{"triage_level":"urgent","summary":"x",'
            '"missing_information":[],"safety_notice":"notice"}'
        )
    with pytest.raises(ValueError, match="safety_notice"):
        parse_triage_output(
            '{"triage_level":"deferred","summary":"x","missing_information":[]}'
        )


def test_summary_keeps_invalid_outputs_visible():
    summary = summarize_baseline_results(
        [
            {
                "expected_level": "maximum",
                "predicted_level": "maximum",
            },
            {
                "expected_level": "moderate",
                "predicted_level": None,
            },
        ]
    )

    assert summary["scenario_count"] == 2
    assert summary["valid_output_count"] == 1
    assert summary["invalid_output_count"] == 1
    assert summary["strict_exact_match_rate"] == 0.5
    assert summary["valid_output_metrics"]["total"] == 1
