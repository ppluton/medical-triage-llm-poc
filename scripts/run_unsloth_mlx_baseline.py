#!/usr/bin/env python3
"""Run deterministic Qwen3 Base inference on the isolated synthetic baseline."""

from __future__ import annotations

import argparse
import json
import platform
import time
from pathlib import Path

from triage_poc.baseline import (
    build_baseline_messages,
    parse_triage_output,
    summarize_baseline_results,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-path", required=True, type=Path)
    parser.add_argument("--scenarios", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--max-new-tokens", type=int, default=384)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def load_scenarios(path: Path) -> list[dict[str, object]]:
    scenarios = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(scenarios, list) or not scenarios:
        raise ValueError("The baseline requires a non-empty JSON scenario list.")
    required = {
        "id",
        "language",
        "category",
        "context",
        "expected_level",
        "clinical_review_status",
    }
    for scenario in scenarios:
        missing = required - scenario.keys()
        if missing:
            raise ValueError(f"Scenario missing fields: {', '.join(sorted(missing))}.")
        if scenario["clinical_review_status"] != "proposed":
            raise ValueError("This runner expects explicitly proposed synthetic references.")
    return scenarios


def main() -> int:
    args = parse_args()
    scenarios = load_scenarios(args.scenarios)
    if not args.model_path.is_dir():
        raise FileNotFoundError(f"Model snapshot not found: {args.model_path}")
    if args.max_new_tokens <= 0:
        raise ValueError("--max-new-tokens must be positive.")
    print(
        f"Baseline preflight passed: scenarios={len(scenarios)}, "
        "model=Qwen3-1.7B-Base, chat_template=qwen3, references=proposed."
    )
    if args.dry_run:
        return 0

    import mlx.core as mx
    import unsloth
    from mlx_lm import generate
    from unsloth import FastLanguageModel

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=str(args.model_path),
        max_seq_length=2048,
        load_in_4bit=True,
        chat_template="qwen3",
        random_state=42,
    )
    results = []
    for scenario in scenarios:
        messages = build_baseline_messages(scenario)
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        started = time.perf_counter()
        raw_output = generate(
            model,
            tokenizer,
            prompt=prompt,
            max_tokens=args.max_new_tokens,
            verbose=False,
        )
        latency_ms = round((time.perf_counter() - started) * 1000, 1)
        try:
            parsed = parse_triage_output(raw_output)
            predicted_level = parsed["triage_level"]
            parse_error = None
        except (ValueError, json.JSONDecodeError) as error:
            parsed = None
            predicted_level = None
            parse_error = str(error)
        results.append(
            {
                "id": scenario["id"],
                "language": scenario["language"],
                "category": scenario["category"],
                "expected_level": scenario["expected_level"],
                "reference_status": scenario["clinical_review_status"],
                "predicted_level": predicted_level,
                "parsed_output": parsed,
                "parse_error": parse_error,
                "raw_output": raw_output,
                "latency_ms": latency_ms,
            }
        )
        print(
            f"{scenario['id']}: predicted={predicted_level or 'invalid'} "
            f"latency_ms={latency_ms}"
        )

    evidence = {
        "status": "observed_synthetic_technical_baseline",
        "base_model_snapshot": str(args.model_path),
        "chat_template": "qwen3",
        "generation": {"deterministic": True, "max_new_tokens": args.max_new_tokens},
        "environment": {
            "python": platform.python_version(),
            "unsloth": getattr(unsloth, "__version__", "unknown"),
            "mlx_device": mx.device_info(),
        },
        "summary": summarize_baseline_results(results),
        "results": results,
        "limits": [
            "All scenarios and expected levels are synthetic and clinically unreviewed.",
            "This run does not establish clinical performance or deployment readiness.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Saved baseline evidence to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
