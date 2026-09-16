"""Text-free replay summary for proposed guardrails over saved endpoint reports."""

from __future__ import annotations

from collections import Counter

from triage_poc.api import ModelResult
from triage_poc.guardrails import apply_proposed_guardrails

_SEVERITY = {"deferred": 0, "moderate": 1, "maximum": 2}


def summarize_guardrail_replay(scenarios: list[dict], reports: dict[str, dict]) -> dict:
    scenario_by_id = {row.get("id"): row for row in scenarios}
    if (
        not scenarios
        or len(scenario_by_id) != len(scenarios)
        or any(row.get("synthetic") is not True for row in scenarios)
    ):
        raise ValueError("Unique synthetic scenarios are required.")
    model_fields = ModelResult.model_fields
    summaries = {}
    for variant, report in sorted(reports.items()):
        records = report.get("records", [])
        record_by_id = {row.get("id"): row for row in records}
        if len(record_by_id) != len(records) or set(record_by_id) != set(scenario_by_id):
            raise ValueError(f"Scenario coverage mismatch for {variant}.")
        statuses: Counter[str] = Counter()
        reasons: Counter[str] = Counter()
        priority_matches = critical_correct = critical_red_flags = 0
        critical_total = uncertainty_correct = uncertainty_total = 0
        for identifier, scenario in scenario_by_id.items():
            record = record_by_id[identifier]
            response = record.get("response")
            if record.get("success") is not True or not isinstance(response, dict):
                raise ValueError(f"Successful response required for {variant}/{identifier}.")
            result = ModelResult.model_validate({key: response[key] for key in model_fields})
            decision = apply_proposed_guardrails(
                scenario["request"]["patient_context"], result, scenario["request"]["language"]
            )
            statuses[decision.status] += 1
            reasons.update(decision.reasons)
            expected = scenario["expected_level"]
            priority_matches += decision.result.triage_level == expected
            if expected == "maximum":
                critical_total += 1
                critical_correct += decision.result.triage_level == "maximum"
                critical_red_flags += bool(decision.result.red_flags)
            if scenario["category"] in {
                "insufficient_information",
                "contradictory_information",
            }:
                uncertainty_total += 1
                uncertainty_correct += (
                    _SEVERITY[decision.result.triage_level] >= _SEVERITY["moderate"]
                )
        total = len(scenarios)
        summaries[variant] = {
            "records": total,
            "guardrail_status_counts": dict(sorted(statuses.items())),
            "guardrail_reason_counts": dict(sorted(reasons.items())),
            "priority_exact_match_rate_after_replay": priority_matches / total,
            "critical_recall_after_replay": critical_correct / critical_total,
            "critical_red_flag_coverage_after_replay": critical_red_flags / critical_total,
            "uncertainty_priority_floor_rate_after_replay": (
                uncertainty_correct / uncertainty_total
            ),
        }
    return {
        "status": "historical_output_replay_not_new_inference",
        "scenario_records": len(scenarios),
        "models": summaries,
        "clinical_validation": "not_performed",
        "limits": [
            "Saved v36 outputs were replayed locally; no model inference was repeated.",
            "Fallback activation does not prove all unsupported claims are detected.",
            "The development set was previously observed and is not a blind final test.",
        ],
    }
