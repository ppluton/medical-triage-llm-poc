"""Conservative final candidate selection from development-only evidence."""

from __future__ import annotations

from typing import Any


def _metric_rows(verified: dict, qualitative: dict) -> dict[str, dict[str, float]]:
    comparison = verified.get("comparison", {})
    review = qualitative.get("models", {})
    rows = {}
    for variant in ("sft", "dpo"):
        current = comparison.get(variant)
        reviewed = review.get(variant)
        if not isinstance(current, dict) or not isinstance(reviewed, dict):
            raise ValueError("SFT and DPO require complete quantitative and qualitative evidence")
        flags = reviewed.get("flag_counts")
        if not isinstance(flags, dict):
            raise ValueError("Qualitative flag counts are required")
        rows[variant] = {
            "mean_example_response_nll": float(current["mean_example_response_nll"]),
            "qa_eos_terminated": float(current["qa_eos_terminated"]),
            "qa_reached_token_cap": float(current["qa_reached_token_cap"]),
            "qa_exact_normalized_reference_matches": float(
                current["qa_exact_normalized_reference_matches"]
            ),
            "qa_empty_outputs": float(current["qa_empty_outputs"]),
            "qa_mean_repeated_token_4gram_fraction": float(
                current["qa_mean_repeated_token_4gram_fraction"]
            ),
            "triage_valid_schema": float(current["triage_valid_schema"]),
            "triage_agreement_on_all_records": float(
                current["triage_agreement_on_all_records"]
            ),
            "critical_valid_maximum": float(current["critical_valid_maximum"]),
            "flagged_records": float(reviewed["flagged_records"]),
            **{f"flag_{name}": float(value) for name, value in sorted(flags.items())},
        }
    if set(rows["sft"]) != set(rows["dpo"]):
        raise ValueError("SFT and DPO metric inventories differ")
    return rows


def select_candidate(verified: dict[str, Any], qualitative: dict[str, Any]) -> dict:
    """Select DPO only when it Pareto-dominates SFT without a safety regression."""
    if verified.get("status") != "saved_metrics_recomputed":
        raise ValueError("Recomputed comparison evidence is required")
    if qualitative.get("status") != "completed_project_review_not_clinical_validation":
        raise ValueError("A complete blinded project review is required")
    rows = _metric_rows(verified, qualitative)
    sft, dpo = rows["sft"], rows["dpo"]
    lower_is_better = {
        "mean_example_response_nll",
        "qa_reached_token_cap",
        "qa_empty_outputs",
        "qa_mean_repeated_token_4gram_fraction",
        "flagged_records",
    } | {
        name for name in sft if name.startswith("flag_")
    }
    regressions = []
    improvements = []
    for name in sorted(sft):
        if name in lower_is_better:
            if dpo[name] > sft[name]:
                regressions.append(name)
            elif dpo[name] < sft[name]:
                improvements.append(name)
        else:
            if dpo[name] < sft[name]:
                regressions.append(name)
            elif dpo[name] > sft[name]:
                improvements.append(name)
    selected = "dpo" if not regressions and improvements else "sft"
    if selected == "dpo":
        rationale = (
            "DPO Pareto-dominates SFT on the reviewed development evidence: no observed "
            "technical or qualitative regression and at least one strict improvement."
        )
    elif regressions:
        rationale = (
            "SFT is retained because DPO regresses on at least one reviewed development "
            "criterion; the held-out reserve was not consulted."
        )
    else:
        rationale = (
            "SFT is retained because DPO does not strictly improve any reviewed development "
            "criterion; the simpler verified adapter is preferred."
        )
    return {
        "status": "selected_for_one_shot_reserve",
        "selected_variant": selected,
        "policy": "dpo_must_pareto_dominate_sft",
        "rationale": rationale,
        "regressions": regressions,
        "improvements": improvements,
        "metrics": rows,
        "held_out_reserve_used": False,
        "clinical_validation": "not_performed",
    }
