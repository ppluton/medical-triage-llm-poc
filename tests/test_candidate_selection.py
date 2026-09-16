"""Verify conservative SFT/DPO selection without held-out data."""

from copy import deepcopy

from triage_poc.candidate_selection import select_candidate


def _evidence():
    row = {
        "mean_example_response_nll": 0.7,
        "qa_eos_terminated": 25,
        "triage_valid_schema": 17,
        "triage_agreement_on_all_records": 0.6,
        "critical_valid_maximum": 7,
    }
    verified = {
        "status": "saved_metrics_recomputed",
        "comparison": {"sft": deepcopy(row), "dpo": deepcopy(row)},
    }
    review = {
        "status": "completed_project_review_not_clinical_validation",
        "models": {
            name: {
                "flagged_records": 3,
                "flag_counts": {
                    "unsupported_clinical_claim": 2,
                    "diagnostic_or_prescriptive_claim": 1,
                    "dangerous_recommendation_or_delay": 0,
                    "malformed_or_repetitive_output": 1,
                },
            }
            for name in ("sft", "dpo")
        },
    }
    return verified, review


def test_retains_sft_when_dpo_is_identical():
    verified, review = _evidence()
    decision = select_candidate(verified, review)
    assert decision["selected_variant"] == "sft"
    assert decision["improvements"] == []
    assert decision["regressions"] == []


def test_selects_dpo_only_for_pareto_improvement():
    verified, review = _evidence()
    verified["comparison"]["dpo"]["qa_eos_terminated"] = 26
    review["models"]["dpo"]["flagged_records"] = 2
    decision = select_candidate(verified, review)
    assert decision["selected_variant"] == "dpo"
    assert set(decision["improvements"]) == {"qa_eos_terminated", "flagged_records"}
    assert decision["regressions"] == []


def test_retains_sft_when_dpo_improves_one_metric_but_regresses_another():
    verified, review = _evidence()
    verified["comparison"]["dpo"]["qa_eos_terminated"] = 26
    verified["comparison"]["dpo"]["critical_valid_maximum"] = 6
    decision = select_candidate(verified, review)
    assert decision["selected_variant"] == "sft"
    assert decision["improvements"] == ["qa_eos_terminated"]
    assert decision["regressions"] == ["critical_valid_maximum"]


def test_retains_sft_when_dpo_has_more_safety_flags():
    verified, review = _evidence()
    review["models"]["dpo"]["flag_counts"]["unsupported_clinical_claim"] = 3
    decision = select_candidate(verified, review)
    assert decision["selected_variant"] == "sft"
    assert decision["regressions"] == ["flag_unsupported_clinical_claim"]
