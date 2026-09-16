"""Convert raw comparison generations into a blinded project-review queue."""

from __future__ import annotations

import hashlib
import random

from triage_poc.api import ModelResult
from triage_poc.safety_evaluation import (
    REVIEW_FLAGS,
    prepare_common_success_blinded_review_queue,
)


def prepare_all_raw_comparison_review(
    scenarios: list[dict], outputs_by_variant: dict[str, list[dict]], *, seed: int
) -> tuple[list[dict], list[dict], dict]:
    """Blind every raw response, including schema-invalid generations."""
    expected_ids = [row.get("id") for row in scenarios]
    if len(expected_ids) != len(set(expected_ids)) or None in expected_ids:
        raise ValueError("Scenario identifiers must be present and unique")
    scenario_by_id = {row["id"]: row for row in scenarios}
    queue, key = [], []
    for variant in ("base", "sft", "dpo"):
        outputs = outputs_by_variant.get(variant)
        if not isinstance(outputs, list) or [row.get("id") for row in outputs] != expected_ids:
            raise ValueError(f"Raw comparison coverage mismatch for {variant}")
        for output in outputs:
            raw = output.get("output")
            if not isinstance(raw, str):
                raise ValueError("Every raw generation must be text")
            try:
                parsed = ModelResult.model_validate_json(raw).model_dump()
                valid_schema = True
            except ValueError:
                parsed = None
                valid_schema = False
            digest = hashlib.sha256(raw.encode()).hexdigest()
            review_id = hashlib.sha256(
                f"{variant}\0{output['id']}\0{digest}".encode()
            ).hexdigest()[:24]
            scenario = scenario_by_id[output["id"]]
            queue.append(
                {
                    "review_id": review_id,
                    "scenario_id": output["id"],
                    "language": scenario["request"]["language"],
                    "category": scenario["category"],
                    "expected_level": scenario["expected_level"],
                    "request": scenario["request"],
                    "raw_output": raw,
                    "valid_schema": valid_schema,
                    "parsed_response": parsed,
                    "review": {flag: None for flag in REVIEW_FLAGS}
                    | {"rationale": None, "reviewer": None, "review_status": "pending"},
                }
            )
            key.append(
                {
                    "review_id": review_id,
                    "scenario_id": output["id"],
                    "variant": variant,
                    "response_sha256": digest,
                }
            )
    random.Random(seed).shuffle(queue)
    coverage = {
        "status": "all_raw_outputs_review_queue_prepared",
        "seed": seed,
        "scenario_records_total": len(scenarios),
        "review_records": len(queue),
        "variants": ["base", "sft", "dpo"],
        "schema_invalid_records": sum(not row["valid_schema"] for row in queue),
        "omissions": [],
        "limits": [
            "Raw development outputs are reviewed even when they violate the JSON schema.",
            "Model identity remains in the separate key until all decisions are complete.",
            "Project review is not healthcare-professional or clinical validation.",
        ],
    }
    return queue, sorted(key, key=lambda item: item["review_id"]), coverage


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
