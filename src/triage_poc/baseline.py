"""Evidence-bounded helpers for the local Qwen synthetic baseline."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from triage_poc.evaluation import TriageComparison, calculate_triage_metrics

TRIAGE_LEVELS = {"maximum", "moderate", "deferred"}
BASELINE_SYSTEM_PROMPT = (
    "You are a medical-triage assistance proof of concept. You do not diagnose, "
    "prescribe, or replace a healthcare professional. Return only one JSON object."
)


def build_baseline_messages(scenario: dict[str, Any]) -> list[dict[str, str]]:
    """Build a stable bilingual-neutral prompt without exposing the expected label."""

    user_prompt = (
        "Assess this synthetic triage scenario and return exactly this JSON shape: "
        '{"triage_level":"maximum|moderate|deferred","summary":"...",'
        '"missing_information":["..."],"safety_notice":"..."}. '
        f"Scenario language: {scenario['language']}. "
        f"Scenario: {scenario['context']}"
    )
    return [
        {"role": "system", "content": BASELINE_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def extract_first_json_object(text: str) -> dict[str, Any]:
    """Extract one balanced JSON object while respecting strings and escapes."""

    start = text.find("{")
    if start < 0:
        raise ValueError("No JSON object found in model output.")
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        character = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                value = json.loads(text[start : index + 1])
                if not isinstance(value, dict):
                    raise ValueError("Parsed JSON value is not an object.")
                return value
    raise ValueError("Model output contains an incomplete JSON object.")


def parse_triage_output(text: str) -> dict[str, Any]:
    """Validate only the minimum baseline output contract needed for comparison."""

    value = extract_first_json_object(text)
    level = value.get("triage_level")
    if level not in TRIAGE_LEVELS:
        raise ValueError(f"Unsupported or missing triage_level: {level!r}.")
    if not isinstance(value.get("summary"), str) or not value["summary"].strip():
        raise ValueError("Missing non-empty summary.")
    if not isinstance(value.get("missing_information"), list):
        raise ValueError("missing_information must be a list.")
    if not isinstance(value.get("safety_notice"), str) or not value["safety_notice"].strip():
        raise ValueError("Missing non-empty safety_notice.")
    return value


def summarize_baseline_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize valid predictions and retain invalid-output coverage explicitly."""

    valid = [result for result in results if result.get("predicted_level") in TRIAGE_LEVELS]
    comparisons = [
        TriageComparison(expected=result["expected_level"], predicted=result["predicted_level"])
        for result in valid
    ]
    metrics = calculate_triage_metrics(comparisons) if comparisons else None
    exact_total = sum(
        result.get("predicted_level") == result["expected_level"] for result in results
    )
    return {
        "scenario_count": len(results),
        "valid_output_count": len(valid),
        "invalid_output_count": len(results) - len(valid),
        "strict_exact_match_rate": exact_total / len(results) if results else None,
        "valid_output_metrics": metrics.__dict__ if metrics else None,
    }


def run_baseline(model_id: str, scenarios_path: Path, output_path: Path) -> None:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype="auto").to(device)
    scenarios = json.loads(scenarios_path.read_text())
    results = []
    for scenario in scenarios:
        prompt = (
            "You are an educational triage POC. Do not diagnose. Return cautious, structured "
            f"follow-up guidance. Scenario: {scenario['context']}"
        )
        inputs = tokenizer(prompt, return_tensors="pt").to(device)
        started = time.perf_counter()
        output = model.generate(**inputs, max_new_tokens=160, do_sample=False)
        text = tokenizer.decode(output[0][inputs.input_ids.shape[1] :], skip_special_tokens=True)
        results.append(
            {
                "id": scenario["id"],
                "output": text,
                "latency_ms": round((time.perf_counter() - started) * 1000, 1),
            }
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            {"model_id": model_id, "device": device, "results": results},
            ensure_ascii=False,
            indent=2,
        )
    )
