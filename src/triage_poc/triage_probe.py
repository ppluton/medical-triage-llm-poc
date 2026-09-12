"""Development-only raw triage evaluation, without post-generation corrections."""

import json

from triage_poc.api import ModelResult, TriageRequest
from triage_poc.evaluation import TriageComparison, calculate_triage_metrics


def messages_for_scenario(row: dict) -> list[dict]:
    request = TriageRequest.model_validate(row["request"])
    return [
        {
            "role": "system",
            "content": (
                "You are an educational medical triage assistant. Do not diagnose or prescribe. "
                "Use only supplied facts. Ask relevant follow-up questions when information is "
                "missing. Request professional assessment for concerning or uncertain symptoms. "
                "Reply in the requested language with only a JSON object matching this schema: "
                + json.dumps(ModelResult.model_json_schema())
            ),
        },
        {"role": "user", "content": request.model_dump_json()},
    ]


def score_outputs(scenarios: list[dict], outputs: list[dict]) -> dict:
    if len(scenarios) != len(outputs) or any(
        row["id"] != output["id"] for row, output in zip(scenarios, outputs, strict=True)
    ):
        raise ValueError("Scenario/output alignment mismatch")
    valid, comparisons, details = 0, [], []
    for row, output in zip(scenarios, outputs, strict=True):
        detail = {
            "id": row["id"],
            "expected_level": row["expected_level"],
            "reference_status": row["reference_status"],
        }
        try:
            result = ModelResult.model_validate_json(output["output"])
            valid += 1
            comparisons.append(TriageComparison(row["expected_level"], result.triage_level))
            detail.update(
                valid_schema=True,
                predicted_level=result.triage_level,
                follow_up_question_count=len(result.follow_up_questions),
                missing_information_count=len(result.missing_information),
            )
        except ValueError:
            detail.update(valid_schema=False, predicted_level=None)
        details.append(detail)
    return {
        "records": len(scenarios),
        "valid_schema": valid,
        "invalid_schema": len(scenarios) - valid,
        "agreement_on_all_records": sum(
            d["predicted_level"] == d["expected_level"] for d in details
        )
        / len(details),
        "valid_only_metrics": calculate_triage_metrics(comparisons).__dict__
        if comparisons
        else None,
        "details": details,
        "clinical_validation": "not_performed",
        "limits": [
            "Proposed synthetic references, not clinical truth.",
            "Question counts do not measure relevance or safety.",
            "Raw generation, no constrained decoding or API guardrails.",
        ],
    }
