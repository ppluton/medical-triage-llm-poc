"""Development-only raw triage evaluation, without post-generation corrections."""

from triage_poc.api import ModelResult, TriageRequest
from triage_poc.evaluation import TriageComparison, calculate_triage_metrics
from triage_poc.triage_prompt import SYSTEM_PROMPT


def messages_for_scenario(row: dict) -> list[dict]:
    request = TriageRequest.model_validate(row["request"])
    return [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
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


def compare_reload(prior: dict, observed: dict) -> dict:
    """Preserve exact reload evidence, including prefix-only and length mismatches."""
    expected = prior["generated_token_ids"]
    actual = observed["generated_token_ids"]
    identical = actual == expected
    first_difference = None
    if not identical:
        first_difference = next(
            (i for i, (a, b) in enumerate(zip(expected, actual)) if a != b),
            min(len(expected), len(actual)),
        )
    return {
        "id": prior["record_id"],
        "identical": identical,
        "first_different_token": first_difference,
        "expected_token_ids": expected,
        "observed": observed,
    }


def inspect_lora_cache(model) -> dict:
    """Count cached inference tensors that no longer match their current weights."""
    import torch

    cached = stale = 0
    for parameter in model.parameters():
        value = getattr(parameter, "_fast_lora", None)
        if value is not None:
            cached += 1
            stale += not torch.equal(value, parameter.detach().to(value.dtype))
    return {"cached_tensors": cached, "stale_tensors": stale}
