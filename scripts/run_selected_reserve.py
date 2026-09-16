#!/usr/bin/env python3
"""Evaluate exactly one selected model on the frozen synthetic triage reserve."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import time
from pathlib import Path

from triage_poc.comparison import sha256
from triage_poc.dpo import (
    adapter_fingerprint,
    load_sft_identity,
    saved_adapter_fingerprint,
    verify_completed_dpo,
)
from triage_poc.final_reserve import validate_frozen_reserve, validate_model_selection
from triage_poc.model_snapshot import verify_base_snapshot
from triage_poc.triage_probe import messages_for_scenario, score_outputs
from triage_poc.triage_prompt import PROMPT_VERSION, SYSTEM_PROMPT


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "selection",
        "comparison-summary",
        "sft-manifest",
        "sft-adapter",
        "dpo-run",
        "reserve-manifest",
        "reserve",
        "development-reference",
        "output",
    ):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Fresh one-shot reserve output required")

    decision = validate_model_selection(args.selection, args.comparison_summary)
    reserve_manifest = validate_frozen_reserve(
        args.reserve_manifest,
        args.reserve,
        args.development_reference,
    )
    selected = decision["selected_variant"]
    identity = load_sft_identity(args.sft_manifest, args.sft_adapter)
    base_snapshot = verify_base_snapshot(Path(identity["base_model"]))
    dpo_proof = verify_completed_dpo(args.dpo_run, args.sft_manifest, args.sft_adapter)
    scenarios = json.loads(args.reserve.read_text())

    os.environ["CUDA_VISIBLE_DEVICES"] = "0"
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, set_seed

    if not torch.cuda.is_available() or "T4" not in torch.cuda.get_device_name(0):
        raise ValueError("Authorized T4 required")
    set_seed(42)
    tokenizer = AutoTokenizer.from_pretrained(args.sft_adapter, local_files_only=True)
    quantization = BitsAndBytesConfig(load_in_4bit=True)
    base = AutoModelForCausalLM.from_pretrained(
        identity["base_model"],
        revision=identity["base_revision"],
        device_map={"": 0},
        torch_dtype=torch.float16,
        quantization_config=quantization,
    )
    model = PeftModel.from_pretrained(base, str(args.sft_adapter), adapter_name="sft")
    if adapter_fingerprint(model, "sft") != saved_adapter_fingerprint(
        args.sft_adapter / "adapter_model.safetensors"
    ):
        raise ValueError("Loaded SFT tensors differ from the saved adapter")
    if selected == "dpo":
        dpo_adapter = args.dpo_run / "adapter/policy"
        model.load_adapter(str(dpo_adapter), adapter_name="dpo", is_trainable=False)
        if adapter_fingerprint(model, "dpo") != saved_adapter_fingerprint(
            dpo_adapter / "adapter_model.safetensors"
        ):
            raise ValueError("Loaded DPO tensors differ from the saved adapter")
        model.set_adapter("dpo")
    else:
        model.set_adapter("sft")
    model.eval()

    def generate(messages: list[dict]) -> dict:
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        inputs = tokenizer(prompt, return_tensors="pt", add_special_tokens=False).to("cuda")
        if inputs.input_ids.shape[1] + 512 > 2048:
            raise ValueError("Prompt exceeds the frozen generation budget")
        torch.cuda.synchronize()
        started = time.perf_counter()
        with torch.inference_mode():
            ids = model.generate(
                **inputs,
                do_sample=False,
                max_new_tokens=512,
                eos_token_id=tokenizer.eos_token_id,
                pad_token_id=tokenizer.pad_token_id,
            )[0, inputs.input_ids.shape[1] :]
        torch.cuda.synchronize()
        tokens = ids.tolist()
        return {
            "output": tokenizer.decode(tokens, skip_special_tokens=True),
            "generated_token_ids": tokens,
            "latency_ms": (time.perf_counter() - started) * 1000,
            "eos_terminated": bool(tokens and tokens[-1] == tokenizer.eos_token_id),
        }

    outputs = []
    for scenario in scenarios:
        outputs.append({"id": scenario["id"], **generate(messages_for_scenario(scenario))})
        print(json.dumps({"stage": selected, "reserve_records": len(outputs)}), flush=True)
    metrics = score_outputs(scenarios, outputs)

    args.output.mkdir(parents=True)
    (args.output / "outputs.json").write_text(
        json.dumps(outputs, ensure_ascii=False, indent=2) + "\n"
    )
    summary = {
        "status": "completed_one_shot_reserve",
        "optimizer_steps": 0,
        "selected_variant": selected,
        "reserve_records_used": len(scenarios),
        "development_records_used": 0,
        "qa_test_records_used": 0,
        "selection_decision_sha256": sha256(args.selection),
        "comparison_summary_sha256": sha256(args.comparison_summary),
        "reserve_manifest_sha256": sha256(args.reserve_manifest),
        "reserve_sha256": reserve_manifest["artifact"]["sha256"],
        "metrics": metrics,
        "dpo_artifact": dpo_proof,
        "prompt_version": PROMPT_VERSION,
        "system_prompt": SYSTEM_PROMPT,
        "quantization": quantization.to_dict(),
        "max_new_tokens": 512,
        "seed": 42,
        "base_model": identity["base_model"],
        "base_revision": identity["base_revision"],
        "base_snapshot": base_snapshot,
        "package_versions": {
            package: importlib.metadata.version(package)
            for package in ("torch", "transformers", "peft", "bitsandbytes")
        },
        "clinical_validation": "not_performed",
        "reuse_policy": "do_not_tune_or_rerun_from_this_result",
    }
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    main()
