"""Convert raw comparison generations into a blinded project-review queue."""

from __future__ import annotations

from triage_poc.api import ModelResult
from triage_poc.safety_evaluation import prepare_common_success_blinded_review_queue


def prepare_raw_comparison_review(
    scenarios: list[dict], outputs_by_variant: dict[str, list[dict]], *, seed: int
) -> tuple[list[dict], list[dict], dict]:
    """Blind every schema-valid response common to all compared variants."""
    expected_ids = [row.get("id") for row in scenarios]
    if len(expected_ids) != len(set(expected_ids)) or None in expected_ids:
        raise ValueError("Scenario identifiers must be present and unique")
    reports = {}
    for variant in ("base", "sft", "dpo"):
        outputs = outputs_by_variant.get(variant)
        if not isinstance(outputs, list) or [row.get("id") for row in outputs] != expected_ids:
            raise ValueError(f"Raw comparison coverage mismatch for {variant}")
        records = []
        for output in outputs:
            try:
                result = ModelResult.model_validate_json(output.get("output"))
            except (TypeError, ValueError):
                records.append(
                    {
                        "id": output["id"],
                        "success": False,
                        "http_status": 422,
                        "failure_code": "invalid_model_result_schema",
                    }
                )
                continue
            records.append(
                {
                    "id": output["id"],
                    "success": True,
                    "http_status": 200,
                    "response": result.model_dump()
                    | {
                        "model_version": variant,
                        "safety_notice": "Raw model generation; API guardrails not applied.",
                        "collection": {},
                    },
                }
            )
        reports[variant] = {"records": records}
    return prepare_common_success_blinded_review_queue(scenarios, reports, seed=seed)
