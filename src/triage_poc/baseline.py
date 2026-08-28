"""Measured local Qwen baseline on proposed synthetic scenarios."""

from __future__ import annotations

import json
import time
from pathlib import Path


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
        results.append({"id": scenario["id"], "output": text, "latency_ms": round((time.perf_counter()-started)*1000, 1)})
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps({"model_id": model_id, "device": device, "results": results}, ensure_ascii=False, indent=2))
