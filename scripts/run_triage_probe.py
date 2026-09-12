#!/usr/bin/env python3
"""Compare Base and SFT on frozen synthetic development scenarios; never train."""

import argparse
import json
import os
import time
from pathlib import Path

from triage_poc.comparison import sha256
from triage_poc.dpo import load_sft_identity
from triage_poc.triage_probe import (
    compare_reload,
    inspect_lora_cache,
    messages_for_scenario,
    score_outputs,
)
from triage_poc.triage_prompt import PROMPT_VERSION, SYSTEM_PROMPT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("sft-manifest", "checkpoint", "scenarios", "prior-qa", "qa-validation", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    identity = load_sft_identity(args.sft_manifest, args.checkpoint)
    scenarios = json.loads(args.scenarios.read_text())
    if not scenarios or any(
        not s.get("synthetic") or s.get("split") != "development" for s in scenarios
    ):
        raise ValueError("Only synthetic development scenarios may be used")
    if args.output.exists():
        raise ValueError("Fresh output required")
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"
    # Import Unsloth first so its patches match the training runtime.
    # isort: off
    from unsloth import FastLanguageModel
    import torch
    from peft import get_peft_model_state_dict, set_peft_model_state_dict
    from safetensors.torch import load_file
    from transformers import AutoTokenizer, set_seed
    # isort: on

    if not torch.cuda.is_available() or "T4" not in torch.cuda.get_device_name(0):
        raise ValueError("Authorized T4 required")
    set_seed(42)
    tokenizer = AutoTokenizer.from_pretrained(args.checkpoint, local_files_only=True)
    model, _ = FastLanguageModel.from_pretrained(
        model_name=identity["base_model"],
        revision=identity["base_revision"],
        max_seq_length=2048,
        dtype=None,
        load_in_4bit=True,
        use_exact_model_name=True,
        device_map={"": 0},
    )
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        lora_alpha=16,
        lora_dropout=0,
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=42,
        use_rslora=False,
    )
    FastLanguageModel.for_inference(model)
    args.output.mkdir(parents=True)

    def generate(messages):
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
        )
        inputs = tokenizer(prompt, return_tensors="pt", add_special_tokens=False).to("cuda")
        if inputs.input_ids.shape[1] + 512 > 2048:
            raise ValueError("Prompt exceeds frozen evaluation budget")
        torch.cuda.synchronize()
        start = time.perf_counter()
        with torch.inference_mode():
            ids = model.generate(
                **inputs,
                do_sample=False,
                max_new_tokens=512,
                eos_token_id=tokenizer.eos_token_id,
                pad_token_id=tokenizer.pad_token_id,
            )[0, inputs.input_ids.shape[1] :].tolist()
        torch.cuda.synchronize()
        return {
            "output": tokenizer.decode(ids, skip_special_tokens=True),
            "generated_token_ids": ids,
            "latency_ms": (time.perf_counter() - start) * 1000,
            "eos_terminated": bool(ids and ids[-1] == tokenizer.eos_token_id),
        }

    summaries = {}
    for stage in ("base", "sft"):
        if stage == "sft":
            cache_report = {"before_load": inspect_lora_cache(model)}
            saved = load_file(str(args.checkpoint / "adapter_model.safetensors"))
            set_peft_model_state_dict(model, saved)
            current = get_peft_model_state_dict(model)
            cache_report["loaded_weights_identical"] = (
                current.keys() == saved.keys()
                and all(torch.equal(current[k].detach().cpu(), saved[k]) for k in saved)
            )
            cache_report["after_load"] = inspect_lora_cache(model)
            # Match the training evaluator's transition and invalidate cached LoRA casts.
            FastLanguageModel.for_training(model, use_gradient_checkpointing="unsloth")
            cache_report["after_reset"] = inspect_lora_cache(model)
            FastLanguageModel.for_inference(model)
            (args.output / "adapter_reload.json").write_text(json.dumps(cache_report, indent=2))
            if (not cache_report["loaded_weights_identical"]
                    or cache_report["after_reset"]["cached_tensors"]):
                raise ValueError("Adapter weights or inference cache did not reset correctly")
            prior = json.loads(args.prior_qa.read_text())["records"]
            validation = {
                r["record_id"]: r
                for r in map(json.loads, args.qa_validation.read_text().splitlines())
            }
            checks = []
            for item in prior:
                observed = generate(validation[item["record_id"]]["messages"][:-1])
                checks.append(compare_reload(item, observed))
                (args.output / "reload.json").write_text(json.dumps(checks, indent=2))
            if not all(c["identical"] for c in checks):
                raise ValueError(
                    "Reload generations differ; inspect runtime before interpreting results"
                )
        outputs = []
        for row in scenarios:
            outputs.append({"id": row["id"], **generate(messages_for_scenario(row))})
            print(
                json.dumps({"stage": stage, "completed": len(outputs), "total": len(scenarios)}),
                flush=True,
            )
        (args.output / f"{stage}.json").write_text(
            json.dumps(outputs, ensure_ascii=False, indent=2)
        )
        summaries[stage] = score_outputs(scenarios, outputs)
    (args.output / "summary.json").write_text(
        json.dumps(
            {
                "status": "completed",
                "prompt_version": PROMPT_VERSION,
                "system_prompt": SYSTEM_PROMPT,
                "optimizer_steps": 0,
                "test_records_used": 0,
                "sft_manifest_sha256": sha256(args.sft_manifest),
                "scenarios_sha256": sha256(args.scenarios),
                "script_sha256": sha256(Path(__file__)),
                "comparison": summaries,
                "reload_identical_generations": len(checks),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
