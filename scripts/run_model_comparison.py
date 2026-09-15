#!/usr/bin/env python3
"""Run matched validation loss and blind-review generations using frozen Kaggle SFT."""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import time
from contextlib import nullcontext
from pathlib import Path

from triage_poc.comparison import (
    BASE_MODEL,
    BASE_REVISION,
    SFT_SHA256,
    encode_example,
    load_validation,
    paired_report,
    select_rows,
    sha256,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validation", required=True, type=Path)
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--sft-adapter", required=True, type=Path)
    parser.add_argument("--dpo-adapter", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--count", type=int, default=500)
    parser.add_argument("--generate-count", type=int, default=30)
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument("--scenario-protocol", type=Path)
    parser.add_argument("--stop-on-message-end", action="store_true")
    parser.add_argument("--precision", choices=["4bit-default", "4bit-nf4", "float16"],
                        default="4bit-default")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output directory exists; choose a fresh run directory.")
    if sha256(args.sft_adapter / "adapter_model.safetensors") != SFT_SHA256:
        raise ValueError("SFT adapter differs from archived best-adapter.")
    rows = select_rows(load_validation(args.validation), args.count, 42)
    metadata = json.loads(args.metadata.read_text())
    if not 0 <= args.generate_count <= args.count or args.max_new_tokens <= 0:
        raise ValueError("Invalid generation limits.")
    for row in rows:
        item = metadata[row["record_id"]]
        if item["split"] != "validation" or item["language"] not in {"fr", "en"}:
            raise ValueError("Invalid validation metadata.")
    protocol = None
    if args.scenario_protocol:
        protocol = json.loads(args.scenario_protocol.read_text())
        if (protocol.get("purpose") != "synthetic_development_schema_probe"
                or not protocol.get("cases")
                or not all(c.get("synthetic") is True for c in protocol["cases"])):
            raise ValueError("Only explicit synthetic development probes are accepted.")
        from jsonschema import Draft202012Validator
        Draft202012Validator.check_schema(protocol["response_schema"])
    if args.dry_run:
        print(json.dumps({"status": "preflight_passed", "records": len(rows),
                          "test_records_used": 0}))
        return

    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, set_seed

    if not torch.cuda.is_available():
        raise RuntimeError("Matched 4-bit evaluation requires CUDA; use private Kaggle.")
    set_seed(42)
    tokenizer = AutoTokenizer.from_pretrained(str(args.sft_adapter))
    generation_options = {}
    if args.stop_on_message_end:
        message_end = tokenizer.convert_tokens_to_ids("<|im_end|>")
        if message_end is None or message_end == tokenizer.unk_token_id:
            raise ValueError("No message-end token found in the archived tokenizer.")
        generation_options["eos_token_id"] = list(dict.fromkeys(
            [tokenizer.eos_token_id, message_end]))
    quantization = None
    if args.precision == "4bit-default":
        quantization = BitsAndBytesConfig(load_in_4bit=True)
    elif args.precision == "4bit-nf4":
        quantization = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.float16)
    base = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL, revision=BASE_REVISION, device_map={"": 0},
        torch_dtype=torch.float16, quantization_config=quantization,
    )
    model = PeftModel.from_pretrained(base, str(args.sft_adapter), adapter_name="sft")
    if args.dpo_adapter:
        model.load_adapter(str(args.dpo_adapter), adapter_name="dpo", is_trainable=False)
    model.eval()
    args.output.mkdir(parents=True)
    encoded = [(row, *encode_example(tokenizer, row["messages"], 2048)) for row in rows]
    variants = {}
    names = ["base", "sft"] + (["dpo"] if args.dpo_adapter else [])
    for name in names:
        variants[name] = []
        if name != "base":
            model.set_adapter(name)
        with model.disable_adapter() if name == "base" else nullcontext():
            for number, (row, token_ids, boundary) in enumerate(encoded):
                inputs = torch.tensor([token_ids], device=model.device)
                with torch.inference_mode():
                    logits = model(input_ids=inputs).logits[:, :-1].float()
                    losses = torch.nn.functional.cross_entropy(
                        logits.reshape(-1, logits.shape[-1]), inputs[:, 1:].reshape(-1),
                        reduction="none")
                    completion = losses[boundary - 1:]
                    record = {
                        "record_id": row["record_id"], **metadata[row["record_id"]],
                        "input_sha256": __import__("hashlib").sha256(
                            json.dumps(token_ids).encode()).hexdigest(),
                        "completion_tokens": completion.numel(),
                        "completion_nll_sum": completion.sum().item(),
                        "sequence_tokens": losses.numel(),
                        "sequence_nll_sum": losses.sum().item(),
                    }
                    del logits, losses, completion
                    if number < args.generate_count:
                        torch.cuda.synchronize()
                        started = time.perf_counter()
                        generated = model.generate(
                            input_ids=inputs[:, :boundary],
                            attention_mask=torch.ones_like(inputs[:, :boundary]),
                            max_new_tokens=args.max_new_tokens, do_sample=False,
                            pad_token_id=tokenizer.eos_token_id, **generation_options)
                        torch.cuda.synchronize()
                        record.update({
                            "generated_token_ids": generated[0, boundary:].tolist(),
                            "output": tokenizer.decode(generated[0, boundary:],
                                                       skip_special_tokens=True),
                            "reference": row["messages"][-1]["content"],
                            "prompt": row["messages"][-2]["content"],
                            "generation_latency_ms": (time.perf_counter() - started) * 1000,
                            "generated_tokens": generated.shape[-1] - boundary,
                            "review_status": "pending",
                        })
                variants[name].append(record)
                with (args.output / f"{name}.jsonl").open("a") as stream:
                    stream.write(json.dumps(record, ensure_ascii=False) + "\n")
                if (number + 1) % 25 == 0:
                    print(f"{name}: {number + 1}/{len(rows)}", flush=True)
    scenario_summary = {}
    if protocol:
        from jsonschema import ValidationError, validate
        for name in names:
            if name != "base":
                model.set_adapter(name)
            valid = 0
            with model.disable_adapter() if name == "base" else nullcontext():
                for case in protocol["cases"]:
                    messages = [{"role": "system", "content": protocol["system_prompt"]
                                 + " Response JSON schema: "
                                 + json.dumps(protocol["response_schema"])},
                                {"role": "user", "content": json.dumps({
                                    "language": case["language"],
                                    "patient_context": case["patient_context"]})}]
                    ids = tokenizer.apply_chat_template(messages, tokenize=True,
                            add_generation_prompt=True, enable_thinking=False)
                    if len(ids) > 2048:
                        raise ValueError("Synthetic probe prompt exceeds context limit.")
                    inputs = torch.tensor([ids], device=model.device)
                    torch.cuda.synchronize()
                    started = time.perf_counter()
                    with torch.inference_mode():
                        generated = model.generate(input_ids=inputs,
                            attention_mask=torch.ones_like(inputs), max_new_tokens=512,
                            do_sample=False, pad_token_id=tokenizer.eos_token_id,
                            **generation_options)
                    torch.cuda.synchronize()
                    output = tokenizer.decode(generated[0, len(ids):], skip_special_tokens=True)
                    schema_valid = False
                    try:
                        validate(json.loads(output), protocol["response_schema"])
                        schema_valid = True
                    except (ValueError, ValidationError):
                        pass
                    valid += int(schema_valid)
                    record = {"id": case["id"], "synthetic": True, "variant": name,
                        "category": case["category"], "language": case["language"],
                        "output": output, "schema_valid": schema_valid,
                        "generated_tokens": generated.shape[-1] - len(ids),
                        "latency_ms": (time.perf_counter() - started) * 1000,
                        "clinical_review_status": "not_performed"}
                    with (args.output / f"{name}-synthetic.jsonl").open("a") as stream:
                        stream.write(json.dumps(record, ensure_ascii=False) + "\n")
            scenario_summary[name] = {"cases": len(protocol["cases"]), "schema_valid": valid}
    summary = {
        "status": "completed", "purpose": "development_validation_comparison",
        "base_model": BASE_MODEL, "base_revision": BASE_REVISION,
        "sft_sha256": SFT_SHA256, "validation_sha256": sha256(args.validation),
        "metadata_sha256": sha256(args.metadata),
        "dpo_sha256": sha256(args.dpo_adapter / "adapter_model.safetensors")
        if args.dpo_adapter else None,
        "code_sha256": {p.name: sha256(p) for p in [
            Path(__file__), Path(__import__("triage_poc.comparison", fromlist=[""]).__file__)]},
        "template_sha256": sha256(args.sft_adapter / "chat_template.jinja"),
        "seed": 42, "count": args.count, "generate_count": args.generate_count,
        "generation": {"max_new_tokens": args.max_new_tokens, "do_sample": False,
                       **generation_options},
        "quantization": args.precision,
        "quantization_config": quantization.to_dict() if quantization else None,
        "device": torch.cuda.get_device_name(0),
        "package_versions": {p: importlib.metadata.version(p) for p in
                             ["torch", "transformers", "peft", "bitsandbytes"]},
        "scenario_protocol_sha256": sha256(args.scenario_protocol) if protocol else None,
        "synthetic_schema_probe": scenario_summary,
        "test_records_used": 0, "comparison": paired_report(variants),
        "clinical_validation": "not_performed",
        "limits": ["Validation guides development; it is not the final test.",
                   "Source-reference likelihood is not medical correctness.",
                   "Generation review is pending; no safety gain is established.",
                   "Latency includes no warmup exclusion and is descriptive only."],
    }
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
