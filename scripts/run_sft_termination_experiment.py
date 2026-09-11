#!/usr/bin/env python3
"""Compare two bounded continuations differing only in the assistant terminator."""

import argparse
import gc
import importlib.metadata
import json
import os
from copy import deepcopy
from pathlib import Path

from triage_poc.comparison import (
    BASE_MODEL,
    BASE_REVISION,
    SFT_SHA256,
    encode_example,
    select_rows,
    sha256,
    validate_conversations,
)
from triage_poc.sft_termination import (
    audit_labels,
    native_eos_template,
    render_prompt_completion,
    render_training_text,
    validate_completion_labels,
)

DATASET_HASHES = {
    "v1": {
        "train": "854ce4f0458d1d313e77d7e3ff9da2d2dffb6571af728a7237f8aada7ce5525d",
        "validation": "7118258c5fdbfe47d5c11b5c4e4b2c2600c4ed17a1eb4b806b0bf5f7c2c52296",
    },
    "v2": {
        "train": "1ec52f47196d8641f317988b398a1d638013a50e04259d870105cb5bcf79cc0a",
        "validation": "e0c3e90f990e9827a0102097bc21d65c479858f3fe66b7d922a2e4ca2a981656",
    },
}


SMOKE_HASHES = {
    "v2": {
        "train": "f628ef9be739039e58ce1e7c620c4c49263a2fba87165c8fe52b29e42e854139",
        "validation": "18aa0849bb4d7ea54d5597a94ed40d605c75be0ef36c9f4b84421b8caa83f1cb",
    }
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--validation", type=Path, required=True)
    parser.add_argument("--sft-adapter", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--arm", choices=["original", "native-eos"], required=True)
    parser.add_argument("--loss-scope", choices=["full", "completion"], default="full")
    parser.add_argument("--input-scope", choices=["full", "smoke"], default="full")
    parser.add_argument("--dataset-version", choices=sorted(DATASET_HASHES), default="v1")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--audit-only", action="store_true")
    args = parser.parse_args()
    if args.loss_scope == "completion" and args.arm != "native-eos":
        raise ValueError("Completion loss requires the native-EOS experiment arm")
    if args.output.exists():
        raise ValueError("Choose a fresh experiment output")
    full_dataset_hashes = DATASET_HASHES[args.dataset_version]
    dataset_hashes = (
        SMOKE_HASHES[args.dataset_version] if args.input_scope == "smoke" else full_dataset_hashes
    )
    expected_train, expected_validation = (64, 3) if args.input_scope == "smoke" else (4000, 500)
    if sha256(args.train) != dataset_hashes["train"]:
        raise ValueError("Training artifact differs from the frozen source bundle")
    if sha256(args.sft_adapter / "adapter_model.safetensors") != SFT_SHA256:
        raise ValueError("Archived SFT checkpoint mismatch")
    train = list(map(json.loads, args.train.read_text().splitlines()))
    validate_conversations(train)
    if len(train) != expected_train:
        raise ValueError("Training count differs from the frozen experiment scope")
    if sha256(args.validation) != dataset_hashes["validation"]:
        raise ValueError("Validation artifact differs from the frozen source bundle")
    validation = list(map(json.loads, args.validation.read_text().splitlines()))
    validate_conversations(validation)
    if len(validation) != expected_validation:
        raise ValueError("Validation count differs from the frozen experiment scope")
    if {r["record_id"] for r in train} & {r["record_id"] for r in validation}:
        raise ValueError("Train/validation IDs overlap")
    train = select_rows(train, 64, 42)
    validation = select_rows(validation, 3, 42)
    if args.dry_run:
        print(
            json.dumps(
                {
                    "status": "preflight_passed",
                    "arm": args.arm,
                    "dataset_version": args.dataset_version,
                    "input_scope": args.input_scope,
                    "loss_scope": args.loss_scope,
                    "train": 64,
                    "validation": 3,
                    "test_records_used": 0,
                }
            )
        )
        return

    os.environ["CUDA_VISIBLE_DEVICES"] = "0"
    # Import order is required: Unsloth patches Transformers and PEFT.
    # isort: off
    from unsloth import FastLanguageModel
    import torch
    from datasets import Dataset
    from peft.utils.save_and_load import load_peft_weights, set_peft_model_state_dict
    from transformers import AutoTokenizer, set_seed
    from trl import SFTConfig, SFTTrainer
    # isort: on

    set_seed(42)

    def restore_model(adapter_directory):
        base, _ = FastLanguageModel.from_pretrained(
            model_name=BASE_MODEL,
            revision=BASE_REVISION,
            max_seq_length=2048,
            dtype=None,
            load_in_4bit=True,
            use_exact_model_name=True,
            device_map={"": 0},
        )
        config = json.loads((adapter_directory / "adapter_config.json").read_text())
        restored = FastLanguageModel.get_peft_model(
            base,
            r=config["r"],
            lora_alpha=config["lora_alpha"],
            lora_dropout=config["lora_dropout"],
            target_modules=config["target_modules"],
            bias="none",
            use_gradient_checkpointing="unsloth",
            random_state=42,
            use_rslora=False,
        )
        state = load_peft_weights(str(adapter_directory), device="cpu")
        loaded = set_peft_model_state_dict(restored, state, adapter_name="default")
        if loaded.unexpected_keys or any("lora_" in k for k in loaded.missing_keys):
            raise ValueError("SFT adapter was not restored completely")
        return restored

    tokenizer = AutoTokenizer.from_pretrained(str(args.sft_adapter))
    reference_tokenizer = tokenizer
    if tokenizer.pad_token_id == tokenizer.eos_token_id:
        raise ValueError("Padding must not mask the native EOS target")
    model = restore_model(args.sft_adapter)
    args.output.mkdir(parents=True)
    eos = tokenizer.eos_token_id
    end = tokenizer.convert_tokens_to_ids("<|im_end|>")
    embeddings = model.get_input_embeddings().weight
    marker_probe = {
        "start_end_embeddings_equal": bool(
            torch.equal(
                embeddings[tokenizer.convert_tokens_to_ids("<|im_start|>")], embeddings[end]
            )
        ),
        "embeddings_trainable": bool(embeddings.requires_grad),
    }
    del embeddings

    def generate(stage):
        FastLanguageModel.for_inference(model)
        model.eval()
        records = []
        for row in validation:
            ids, boundary = encode_example(tokenizer, row["messages"], 2048)
            inputs = torch.tensor([ids[:boundary]], device=model.device)
            reference_ids = tokenizer.encode(
                render_training_text(reference_tokenizer, row, True), add_special_tokens=False
            )
            assert reference_ids[-1] == eos
            with torch.inference_mode():
                logits = (
                    model(input_ids=torch.tensor([reference_ids[:-1]], device=model.device))
                    .logits[0, -1]
                    .float()
                )
                native_eos_probability = torch.softmax(logits, dim=-1)[eos].item()
                del logits
                output = model.generate(
                    input_ids=inputs,
                    attention_mask=torch.ones_like(inputs),
                    max_new_tokens=256,
                    do_sample=False,
                    eos_token_id=[eos, end],
                    pad_token_id=tokenizer.pad_token_id,
                )
            output_ids = output[0, boundary:].tolist()
            records.append(
                {
                    "record_id": row["record_id"],
                    "stage": stage,
                    "generated_token_ids": output_ids,
                    "generated_tokens": len(output_ids),
                    "output": tokenizer.decode(output_ids, skip_special_tokens=True),
                    "native_eos_probability_after_source_answer": native_eos_probability,
                }
            )
        (args.output / f"{stage}.jsonl").write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records)
        )
        print(
            json.dumps(
                {"stage": stage, "generated_tokens": [r["generated_tokens"] for r in records]}
            ),
            flush=True,
        )
        return records

    if not args.audit_only:
        generate("before")
    FastLanguageModel.for_training(model, use_gradient_checkpointing="unsloth")
    texts = [render_training_text(tokenizer, row, args.arm == "native-eos") for row in train]
    if any(len(tokenizer.encode(text, add_special_tokens=False)) > 2048 for text in texts):
        raise ValueError("No silent truncation is allowed in this experiment")
    prompt_completion_rows = ([render_prompt_completion(tokenizer, row) for row in train]
                              if args.loss_scope == "completion" else [])
    dataset = (
        Dataset.from_list(prompt_completion_rows)
        if args.loss_scope == "completion"
        else Dataset.from_dict({"text": texts})
    )
    training_args = SFTConfig(
        output_dir=str(args.output / "trainer"),
        max_steps=20,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=8,
        learning_rate=1e-4,
        warmup_steps=3,
        lr_scheduler_type="linear",
        optim="adamw_torch",
        weight_decay=0.001,
        fp16=True,
        bf16=False,
        logging_steps=1,
        eval_strategy="no",
        save_strategy="no",
        report_to="none",
        seed=42,
        data_seed=42,
        max_length=2048,
        packing=False,
        completion_only_loss=args.loss_scope == "completion",
        dataset_text_field="text",
        dataset_num_proc=1,
    )
    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,
        train_dataset=dataset,
        args=training_args,
    )
    audits = []
    for i in range(len(trainer.train_dataset)):
        batch = trainer.data_collator([trainer.train_dataset[i]])
        audit = audit_labels(batch, eos, end)
        if args.loss_scope == "completion":
            full_ids = tokenizer.encode(texts[i], add_special_tokens=False)
            if trainer.train_dataset[i]["input_ids"] != full_ids:
                raise ValueError("Trainer changed the exact completion training tokens")
            boundary = len(
                tokenizer.encode(prompt_completion_rows[i]["prompt"], add_special_tokens=False)
            )
            audit.update(
                validate_completion_labels(batch["labels"].flatten().tolist(), full_ids, boundary)
            )
        audits.append(audit)
    expected_eos = 1 if args.arm == "native-eos" else 0
    if any(a["supervised_native_eos"] != expected_eos for a in audits):
        raise ValueError("Actual trainer EOS labels differ from the experiment design")
    (args.output / "label-audit.json").write_text(json.dumps(audits, indent=2))
    if args.audit_only:
        summary = {
            "status": "actual_trainer_labels_audited",
            "arm": args.arm,
            "training_steps": 0,
            "train_records": len(train),
            "test_records_used": 0,
            "initial_sft_sha256": SFT_SHA256,
            "dataset_version": args.dataset_version,
            "input_scope": args.input_scope,
            "loss_scope": args.loss_scope,
            "train_sha256": dataset_hashes["train"],
            "full_dataset_hashes": full_dataset_hashes,
            "native_eos_label_counts": [a["supervised_native_eos"] for a in audits],
            "marker_probe": marker_probe,
            "code_sha256": sha256(Path(__file__)),
        }
        (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps(summary), flush=True)
        return
    result = trainer.train()
    trainer.save_model(str(args.output / "adapter"))
    exported_tokenizer = deepcopy(tokenizer)
    if args.arm == "native-eos":
        exported_tokenizer.chat_template = native_eos_template(tokenizer.chat_template)
    exported_tokenizer.save_pretrained(str(args.output / "adapter"))
    reloaded_tokenizer = AutoTokenizer.from_pretrained(
        str(args.output / "adapter"), local_files_only=True
    )
    for row in train + validation:
        actual = reloaded_tokenizer.apply_chat_template(
            row["messages"], tokenize=False, add_generation_prompt=False
        )
        expected = render_training_text(tokenizer, row, args.arm == "native-eos")
        if actual != expected:
            raise ValueError("Exported tokenizer changes the training format")
    after = generate("after")
    initial_weights = load_peft_weights(str(args.sft_adapter), device="cpu")
    saved_weights = load_peft_weights(str(args.output / "adapter"), device="cpu")
    if initial_weights.keys() != saved_weights.keys():
        raise ValueError("Saved adapter tensor inventory differs from the initial SFT")
    changed_tensors = sum(
        not torch.equal(initial_weights[key], saved_weights[key]) for key in initial_weights
    )
    if not changed_tensors or any(
        not torch.isfinite(value).all() for value in saved_weights.values()
    ):
        raise ValueError("Training must change adapter weights and preserve finite tensors")
    del initial_weights, saved_weights
    del trainer
    del model
    gc.collect()
    torch.cuda.empty_cache()
    model = restore_model(args.output / "adapter")
    tokenizer = reloaded_tokenizer
    reloaded = generate("reloaded")
    if [r["generated_token_ids"] for r in after] != [r["generated_token_ids"] for r in reloaded]:
        raise ValueError("Saved checkpoint does not reproduce deterministic generation")
    summary = {
        "status": "completed",
        "purpose": "controlled_sft_termination_experiment",
        "checkpoint_reload_generation": "passed_on_three_development_examples",
        "changed_adapter_tensors": changed_tensors,
        "arm": args.arm,
        "base_model": BASE_MODEL,
        "base_revision": BASE_REVISION,
        "initial_sft_sha256": SFT_SHA256,
        "dataset_version": args.dataset_version,
        "input_scope": args.input_scope,
        "loss_scope": args.loss_scope,
        "train_sha256": dataset_hashes["train"],
        "full_dataset_hashes": full_dataset_hashes,
        "validation_sha256": sha256(args.validation),
        "seed": 42,
        "train_ids": [r["record_id"] for r in train],
        "validation_ids": [r["record_id"] for r in validation],
        "training_args": training_args.to_dict(),
        "train_metrics": result.metrics,
        "marker_probe": marker_probe,
        "test_records_used": 0,
        "code_sha256": sha256(Path(__file__)),
        "adapter_sha256": sha256(args.output / "adapter/adapter_model.safetensors"),
        "package_versions": {
            p: importlib.metadata.version(p)
            for p in ["unsloth", "unsloth_zoo", "torch", "transformers", "trl", "peft"]
        },
        "limits": [
            "64 training rows and three development validations only.",
            "Both arms restart the optimizer from the same SFT weights.",
            "This is a termination experiment, not a clinical quality evaluation.",
        ],
    }
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"status": "completed", "arm": args.arm}), flush=True)


if __name__ == "__main__":
    main()
