#!/usr/bin/env python3
"""Check archived SFT generations with the original training backend."""
import argparse
import importlib.metadata
import json
import os
from contextlib import nullcontext
from pathlib import Path

from triage_poc.comparison import (
    BASE_MODEL,
    BASE_REVISION,
    SFT_SHA256,
    encode_example,
    load_validation,
    select_rows,
    sha256,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validation", type=Path, required=True)
    parser.add_argument("--sft-adapter", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Choose a new diagnostic output directory")
    if sha256(args.sft_adapter / "adapter_model.safetensors") != SFT_SHA256:
        raise ValueError("Archived SFT checksum mismatch")
    rows = select_rows(load_validation(args.validation), 3, 42)
    import torch
    from peft import PeftModel
    from transformers import AutoTokenizer, set_seed
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"
    from unsloth import FastLanguageModel

    set_seed(42)
    base, _ = FastLanguageModel.from_pretrained(
        model_name=BASE_MODEL, revision=BASE_REVISION, max_seq_length=2048,
        dtype=None, load_in_4bit=True, use_exact_model_name=True, device_map={"": 0})
    tokenizer = AutoTokenizer.from_pretrained(str(args.sft_adapter))
    token_probe = {}
    for token in ["<|endoftext|>", "<|im_start|>", "<|im_end|>", "完整热"]:
        token_id = tokenizer.convert_tokens_to_ids(token)
        token_probe[token] = {"token_id": token_id,
            "input_norm": base.get_input_embeddings().weight[token_id].float().norm().item(),
            "output_norm": base.get_output_embeddings().weight[token_id].float().norm().item()}
    print(json.dumps({"token_embedding_probe": token_probe}), flush=True)
    model = PeftModel.from_pretrained(base, str(args.sft_adapter), adapter_name="sft")
    FastLanguageModel.for_inference(model)
    model.eval()
    args.output.mkdir(parents=True)
    for name in ["base", "sft"]:
        if name == "sft":
            model.set_adapter("sft")
        with model.disable_adapter() if name == "base" else nullcontext():
            for row in rows:
                ids, boundary = encode_example(tokenizer, row["messages"], 2048)
                inputs = torch.tensor([ids[:boundary]], device=model.device)
                with torch.inference_mode():
                    generated = model.generate(input_ids=inputs,
                        attention_mask=torch.ones_like(inputs), max_new_tokens=256,
                        do_sample=False, pad_token_id=tokenizer.eos_token_id,
                        eos_token_id=[151643, 151645])
                output_ids = generated[0, boundary:].tolist()
                record = {"record_id": row["record_id"], "variant": name,
                    "generated_token_ids": output_ids, "generated_tokens": len(output_ids),
                    "output": tokenizer.decode(output_ids, skip_special_tokens=True)}
                with (args.output / f"{name}.jsonl").open("a") as stream:
                    stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    summary = {"status": "completed", "purpose": "original_backend_generation_diagnostic",
        "sft_sha256": SFT_SHA256, "base_model": BASE_MODEL, "base_revision": BASE_REVISION,
        "validation_sha256": sha256(args.validation), "count": 3, "test_records_used": 0,
        "code_sha256": sha256(Path(__file__)), "token_embedding_probe": token_probe,
        "generation": {"do_sample": False, "max_new_tokens": 256,
                       "eos_token_id": [151643, 151645]},
        "package_versions": {p: importlib.metadata.version(p) for p in [
            "unsloth", "unsloth_zoo", "torch", "transformers", "peft", "bitsandbytes"]},
        "clinical_validation": "not_performed"}
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
