#!/usr/bin/env python3
"""Train a bounded DPO adapter from the archived SFT, with a frozen SFT reference."""
import argparse
import importlib.metadata
import json
from pathlib import Path

from triage_poc.comparison import BASE_MODEL, BASE_REVISION, SFT_SHA256, sha256
from triage_poc.dpo import load_dpo_handoff


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("dataset", "comparison", "decision", "sft-adapter", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--max-steps", type=int, default=20)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.max_steps <= 500:
        raise ValueError("A bounded run requires 1 to 500 optimizer steps.")
    if args.output.exists():
        raise ValueError("Use a fresh DPO output directory.")
    if sha256(args.sft_adapter / "adapter_model.safetensors") != SFT_SHA256:
        raise ValueError("DPO must start from the archived SFT.")
    manifest, rows = load_dpo_handoff(args.dataset, args.comparison, args.decision)
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(str(args.sft_adapter))
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"
    rendered_splits = {}
    for split, records in rows.items():
        rendered = []
        for row in records:
            prompt = tokenizer.apply_chat_template(
                [{"role": "user", "content": row["prompt"]}], tokenize=False,
                add_generation_prompt=True, enable_thinking=False)
            chosen = row["chosen"] + tokenizer.eos_token
            rejected = row["rejected"] + tokenizer.eos_token
            if len(tokenizer.encode(prompt, add_special_tokens=False)) > 1024:
                raise ValueError("DPO prompt exceeds limit; review data, do not truncate silently.")
            if max(len(tokenizer.encode(prompt + answer, add_special_tokens=False))
                   for answer in (chosen, rejected)) > 2048:
                raise ValueError("DPO sequence exceeds limit; review data before training.")
            rendered.append({"prompt": prompt, "chosen": chosen, "rejected": rejected})
        rendered_splits[split] = rendered
    if args.dry_run:
        print(json.dumps({"status": "preflight_passed", "test_records_used": 0,
                          "records": {k: len(v) for k, v in rows.items()}}))
        return
    import torch
    from datasets import Dataset
    from peft import PeftModel, prepare_model_for_kbit_training
    from transformers import AutoModelForCausalLM, BitsAndBytesConfig, set_seed
    from trl import DPOConfig, DPOTrainer

    if not torch.cuda.is_available():
        raise RuntimeError("This recipe requires the authorized private CUDA environment.")
    if importlib.metadata.version("trl") != "0.23.1":
        raise RuntimeError("This recipe requires TRL 0.23.1.")
    set_seed(42)
    base = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL, revision=BASE_REVISION, device_map={"": 0}, torch_dtype=torch.float16,
        quantization_config=BitsAndBytesConfig(load_in_4bit=True))
    base = prepare_model_for_kbit_training(base)
    # Two copies of the same SFT: policy is trainable; reference stays frozen.
    model = PeftModel.from_pretrained(base, str(args.sft_adapter),
                                      adapter_name="policy", is_trainable=True)
    model.load_adapter(str(args.sft_adapter), adapter_name="reference", is_trainable=False)
    model.set_adapter("policy")
    model.config.use_cache = False
    datasets = {split: Dataset.from_list(records)
                for split, records in rendered_splits.items()}
    config = DPOConfig(
        output_dir=str(args.output), max_steps=args.max_steps, beta=0.1, learning_rate=5e-6,
        per_device_train_batch_size=1, per_device_eval_batch_size=1,
        gradient_accumulation_steps=8, max_length=2048, max_prompt_length=1024,
        model_adapter_name="policy", ref_adapter_name="reference",
        gradient_checkpointing=True, fp16=True, bf16=False, seed=42, data_seed=42,
        eval_strategy="steps", eval_steps=10, save_strategy="steps", save_steps=10,
        save_total_limit=2, logging_steps=1, report_to="none", push_to_hub=False,
    )
    trainer = DPOTrainer(model=model, args=config, processing_class=tokenizer,
                         train_dataset=datasets["train"], eval_dataset=datasets["validation"])
    result = trainer.train()
    model.save_pretrained(args.output / "adapter", selected_adapters=["policy"])
    tokenizer.save_pretrained(args.output / "adapter" / "policy")
    summary = {
        "status": "completed_educational_dpo", "clinical_validation": "not_performed",
        "base_model": BASE_MODEL, "base_revision": BASE_REVISION,
        "sft_sha256": SFT_SHA256, "reference": "frozen_archived_sft",
        "dataset_manifest_sha256": sha256(args.dataset / "manifest.json"),
        "comparison_sha256": sha256(args.comparison), "decision_sha256": sha256(args.decision),
        "script_sha256": sha256(Path(__file__)), "config": config.to_dict(),
        "train_metrics": result.metrics, "test_records_used": 0,
        "package_versions": {p: importlib.metadata.version(p) for p in
                             ["torch", "transformers", "peft", "trl", "datasets"]},
        "dataset_status": manifest["status"],
    }
    (args.output / "run_summary.json").write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    main()
