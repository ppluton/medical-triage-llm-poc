#!/usr/bin/env python3
"""Compare current Base/SFT/DPO on identical frozen inputs without training."""

import argparse
import importlib.metadata
import json
import os
import time
from contextlib import nullcontext
from pathlib import Path

from triage_poc.comparison import sha256, validate_conversations
from triage_poc.dpo import (
    adapter_fingerprint,
    load_sft_identity,
    saved_adapter_fingerprint,
    verify_completed_dpo,
)
from triage_poc.final_selection import select_generation_ids, validate_final_freeze
from triage_poc.sft_termination import render_prompt_completion
from triage_poc.triage_probe import messages_for_scenario, score_outputs
from triage_poc.triage_prompt import PROMPT_VERSION, SYSTEM_PROMPT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "sft-manifest",
        "sft-adapter",
        "dpo-run",
        "data-manifest",
        "output",
    ):
        parser.add_argument("--" + name, type=Path, required=True)
    for name in ("validation", "prior-qa", "scenarios", "test", "final-freeze"):
        parser.add_argument("--" + name, type=Path)
    args = parser.parse_args()
    final = args.test is not None
    if final:
        if args.final_freeze is None or any((args.validation, args.prior_qa, args.scenarios)):
            raise ValueError("Final mode requires test and freeze only, without development inputs")
    elif args.final_freeze or not all((args.validation, args.prior_qa, args.scenarios)):
        raise ValueError("Development mode requires validation, prior QA and scenarios")
    if args.output.exists():
        raise ValueError("Fresh comparison output required")
    identity = load_sft_identity(args.sft_manifest, args.sft_adapter)
    dpo_proof = verify_completed_dpo(args.dpo_run, args.sft_manifest, args.sft_adapter)
    print(json.dumps({"stage": "artifact_verified", **dpo_proof}), flush=True)
    manifest = json.loads(args.data_manifest.read_text())
    dataset = args.test if final else args.validation
    freeze = None
    if final:
        freeze = json.loads(args.final_freeze.read_text())
        frozen_paths = {
            "test": args.test,
            "data_manifest": args.data_manifest,
            "sft_manifest": args.sft_manifest,
            "dpo_summary": args.dpo_run / "run_summary.json",
            "runner": Path(__file__),
            "selection": Path(__file__).resolve().parents[1] / "src/triage_poc/final_selection.py",
            "termination": Path(__file__).resolve().parents[1]
            / "src/triage_poc/sft_termination.py",
        }
        validate_final_freeze(freeze, {key: sha256(path) for key, path in frozen_paths.items()})
    artifact_key = "test_qwen3" if final else "validation_qwen3"
    if artifact_key not in manifest["artifacts"]:
        raise ValueError("Required rendered split is absent; prepare and verify its manifest first")
    entry = manifest["artifacts"][artifact_key]
    if sha256(dataset) != entry["sha256"]:
        raise ValueError("Dataset checksum mismatch")
    rows = [json.loads(line) for line in dataset.read_text().splitlines()]
    validate_conversations(rows)
    if len(rows) != entry["record_count"] or (final and len(rows) != 500):
        raise ValueError("Dataset count mismatch")
    by_id = {r["record_id"]: r for r in rows}
    if final:
        selected = select_generation_ids(by_id)
        scenarios = []
    else:
        selected = [r["record_id"] for r in json.loads(args.prior_qa.read_text())["records"]]
        if len(selected) != 30 or len(set(selected)) != 30 or not set(selected) <= by_id.keys():
            raise ValueError("Expected the thirty frozen QA development prompts")
        scenarios = json.loads(args.scenarios.read_text())
        if not scenarios or any(
            r.get("synthetic") is not True or r.get("split") != "development" for r in scenarios
        ):
            raise ValueError("Only synthetic development scenarios may be used")
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, set_seed

    if not torch.cuda.is_available() or "T4" not in torch.cuda.get_device_name(0):
        raise ValueError("Authorized T4 required")
    if final and any(
        importlib.metadata.version(name) != version
        for name, version in freeze["package_versions"].items()
    ):
        raise ValueError("Runtime differs from final freeze")
    set_seed(42)
    tokenizer = AutoTokenizer.from_pretrained(args.sft_adapter, local_files_only=True)
    # Match the DPO runner, and record the effective quantization settings.
    quantization = BitsAndBytesConfig(load_in_4bit=True)
    base = AutoModelForCausalLM.from_pretrained(
        identity["base_model"],
        revision=identity["base_revision"],
        device_map={"": 0},
        torch_dtype=torch.float16,
        quantization_config=quantization,
    )
    model = PeftModel.from_pretrained(base, str(args.sft_adapter), adapter_name="sft")
    model.load_adapter(str(args.dpo_run / "adapter/policy"), adapter_name="dpo", is_trainable=False)
    for name, path in (("sft", args.sft_adapter), ("dpo", args.dpo_run / "adapter/policy")):
        if adapter_fingerprint(model, name) != saved_adapter_fingerprint(
            path / "adapter_model.safetensors"
        ):
            raise ValueError("Loaded adapter tensors differ from saved weights")
    model.eval()
    args.output.mkdir(parents=True)
    if final:
        (args.output / "final_freeze.json").write_text(json.dumps(freeze, indent=2))
        (args.output / "selected_ids.json").write_text(json.dumps(selected, indent=2))
    encoded = []
    for row in rows:
        rendered = render_prompt_completion(tokenizer, row)
        tokens = tokenizer.encode(
            rendered["prompt"] + rendered["completion"], add_special_tokens=False
        )
        boundary = len(tokenizer.encode(rendered["prompt"], add_special_tokens=False))
        if len(tokens) > 2048 or tokens[boundary:].count(tokenizer.eos_token_id) != 1:
            raise ValueError("Invalid current SFT completion budget or EOS")
        encoded.append((row["record_id"], tokens, boundary))

    def generate(messages):
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
        )
        inputs = tokenizer(prompt, return_tensors="pt", add_special_tokens=False).to("cuda")
        if inputs.input_ids.shape[1] + 512 > 2048:
            raise ValueError("Prompt exceeds the common generation budget")
        torch.cuda.synchronize()
        start = time.perf_counter()
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
            "latency_ms": (time.perf_counter() - start) * 1000,
            "eos_terminated": bool(tokens and tokens[-1] == tokenizer.eos_token_id),
        }

    comparison = {}
    for stage in ("base", "sft", "dpo"):
        if stage != "base":
            model.set_adapter(stage)
        model.eval()
        with model.disable_adapter() if stage == "base" else nullcontext():
            losses = []
            for index, (identifier, tokens, boundary) in enumerate(encoded):
                inputs = torch.tensor([tokens], device="cuda")
                labels = inputs.clone()
                labels[:, :boundary] = -100
                with torch.inference_mode():
                    loss = model(input_ids=inputs, labels=labels).loss.float().item()
                if not __import__("math").isfinite(loss):
                    raise ValueError("Non-finite validation loss")
                losses.append({"record_id": identifier, "response_nll": loss})
                if (index + 1) % 50 == 0:
                    print(json.dumps({"stage": stage, "loss_records": index + 1}), flush=True)
            qa = [
                {"record_id": identifier, **generate(by_id[identifier]["messages"][:-1])}
                for identifier in selected
            ]
            triage = []
            for row in scenarios:
                triage.append({"id": row["id"], **generate(messages_for_scenario(row))})
                print(json.dumps({"stage": stage, "triage_records": len(triage)}), flush=True)
        result = {"losses": losses, "qa": qa, "triage": triage}
        (args.output / f"{stage}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
        comparison[stage] = {
            "mean_example_response_nll": sum(r["response_nll"] for r in losses) / len(losses),
            "loss_records": len(losses),
            "qa_eos_terminated": sum(r["eos_terminated"] for r in qa),
            "triage": score_outputs(scenarios, triage) if scenarios else None,
        }
    summary = {
        "status": "completed",
        "optimizer_steps": 0,
        "test_records_used": len(rows) if final else 0,
        "evaluation_split": "test" if final else "validation",
        "comparison": comparison,
        "dpo_artifact": dpo_proof,
        "prompt_version": PROMPT_VERSION,
        "system_prompt": SYSTEM_PROMPT,
        "quantization": quantization.to_dict(),
        "max_new_tokens": 512,
        "seed": 42,
        "base_model": identity["base_model"],
        "base_revision": identity["base_revision"],
        "input_hashes": {
            name: sha256(getattr(args, name))
            for name in (
                "sft_manifest",
                "data_manifest",
                "validation",
                "prior_qa",
                "scenarios",
                "test",
                "final_freeze",
            )
            if getattr(args, name) is not None
        },
        "script_sha256": sha256(Path(__file__)),
        "package_versions": {
            p: importlib.metadata.version(p)
            for p in ("torch", "transformers", "peft", "bitsandbytes")
        },
        "clinical_validation": "not_performed",
    }
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    main()
