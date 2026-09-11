#!/usr/bin/env python3
"""Prepare or explicitly execute the bounded source SFT pilot from the pinned base."""

import argparse
import json
import math
import os
from copy import deepcopy
from pathlib import Path

from triage_poc.comparison import sha256, validate_conversations
from triage_poc.sft_pilot import PilotBudget, require_complete_checkpoint, validate_pilot_config
from triage_poc.sft_termination import (
    native_eos_template,
    render_prompt_completion,
    validate_completion_labels,
)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("config", "data", "tokenizer", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--execute-pilot", action="store_true")
    a = p.parse_args()
    cfg = json.loads(a.config.read_text())
    validate_pilot_config(cfg)
    loaded = []
    for key, name in [
        ("train_qwen3", "train-qwen3.jsonl"),
        ("validation_qwen3", "validation-qwen3.jsonl"),
    ]:
        file = a.data / name
        if sha256(file) != cfg["artifact_hashes"][key]:
            raise ValueError("Pilot rendered artifact changed")
        rows = [json.loads(line) for line in file.read_text().splitlines()]
        validate_conversations(rows)
        loaded.append(rows)
    train, validation = loaded
    if {r["record_id"] for r in train} & {r["record_id"] for r in validation}:
        raise ValueError("Pilot train/validation IDs overlap")
    for name, expected in cfg["tokenizer_files_sha256"].items():
        if sha256(a.tokenizer / name) != expected:
            raise ValueError("Frozen pilot tokenizer changed")
    if (len(train), len(validation)) != (cfg["training_records"], cfg["validation_records"]):
        raise ValueError("Pilot split counts changed")
    validation_by_id = {r["record_id"]: r for r in validation}
    generation = [validation_by_id[rid] for rid in cfg["evaluation"]["generation_record_ids"]]

    if len(generation) != cfg["evaluation"]["generation_records"] or len(
        {r["record_id"] for r in generation}
    ) != len(generation):
        raise ValueError("Invalid frozen generation selection")
    if a.output.exists():
        raise ValueError("Fresh output required; continuation is a separate reviewed operation")
    if not a.execute_pilot:
        print(
            json.dumps(
                {
                    "status": "preflight_passed_not_launched",
                    "train": len(train),
                    "validation": len(validation),
                    "test_records_used": 0,
                    "training_steps": 0,
                }
            )
        )
        return
    import importlib.metadata as metadata

    for package, expected in cfg["runtime_versions"].items():
        if metadata.version(package) != expected:
            raise ValueError(f"Pinned runtime mismatch: {package}")
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"
    # Unsloth must patch Transformers before the trainer/model imports.
    # isort: off
    from unsloth import FastLanguageModel
    import torch
    from datasets import Dataset
    from peft import get_peft_model_state_dict
    from transformers import AutoTokenizer, TrainerCallback, set_seed
    from trl import SFTConfig, SFTTrainer
    # isort: on

    if not torch.cuda.is_available() or "T4" not in torch.cuda.get_device_name(0):
        raise ValueError("This pilot is restricted to the authorized free T4 environment")
    set_seed(cfg["seed"])
    tokenizer = AutoTokenizer.from_pretrained(str(a.tokenizer), local_files_only=True)
    train_pairs = [render_prompt_completion(tokenizer, r) for r in train]
    val_pairs = [render_prompt_completion(tokenizer, r) for r in validation]
    for pair in train_pairs + val_pairs:
        ids = tokenizer.encode(pair["prompt"] + pair["completion"], add_special_tokens=False)
        if len(ids) > cfg["max_length"] or ids[-1] != tokenizer.eos_token_id:
            raise ValueError("Invalid response length or EOS")
    model, _ = FastLanguageModel.from_pretrained(
        model_name=cfg["base_model"],
        revision=cfg["base_revision"],
        max_seq_length=cfg["max_length"],
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
        random_state=cfg["seed"],
        use_rslora=False,
    )
    initial_adapter = {
        k: value.detach().cpu().clone() for k, value in get_peft_model_state_dict(model).items()
    }
    a.output.mkdir(parents=True)
    budget = PilotBudget(cfg["pilot_stop_after_steps"], cfg["pilot_training_wall_seconds"])

    class BoundedTraining(TrainerCallback):
        def on_train_begin(self, args, state, control, **kwargs):
            budget.start()

        def on_step_end(self, args, state, control, **kwargs):
            if budget.reached(state.global_step):
                control.should_training_stop = True
                control.should_save = True
            return control

        def on_log(self, args, state, control, logs=None, **kwargs):
            for key in ("loss", "grad_norm", "eval_loss"):
                if logs and key in logs and not math.isfinite(float(logs[key])):
                    raise ValueError("Non-finite training metric")

    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,
        train_dataset=Dataset.from_list(train_pairs),
        eval_dataset=Dataset.from_list(val_pairs),
        args=SFTConfig(
            output_dir=str(a.output / "trainer"),
            max_steps=cfg["scheduler_horizon_steps"],
            per_device_train_batch_size=1,
            gradient_accumulation_steps=cfg["gradient_accumulation_steps"],
            per_device_eval_batch_size=1,
            learning_rate=cfg["learning_rate"],
            warmup_steps=cfg["warmup_steps"],
            lr_scheduler_type=cfg["lr_scheduler_type"],
            optim="adamw_torch",
            weight_decay=0.001,
            fp16=True,
            bf16=False,
            logging_steps=1,
            logging_nan_inf_filter=False,
            eval_strategy="steps",
            eval_steps=cfg["save_steps"],
            prediction_loss_only=True,
            save_strategy="steps",
            save_steps=cfg["save_steps"],
            save_only_model=False,
            save_total_limit=4,
            load_best_model_at_end=False,
            report_to="none",
            seed=cfg["seed"],
            data_seed=cfg["seed"],
            max_length=cfg["max_length"],
            completion_only_loss=True,
            packing=False,
            dataset_num_proc=1,
        ),
        callbacks=[BoundedTraining()],
    )
    for dataset, pairs in [(trainer.train_dataset, train_pairs), (trainer.eval_dataset, val_pairs)]:
        for i, pair in enumerate(pairs):
            ids = tokenizer.encode(pair["prompt"] + pair["completion"], add_special_tokens=False)
            if dataset[i]["input_ids"] != ids:
                raise ValueError("Trainer tokenization changed")
            labels = trainer.data_collator([dataset[i]])["labels"].flatten().tolist()
            boundary = len(tokenizer.encode(pair["prompt"], add_special_tokens=False))
            validate_completion_labels(labels, ids, boundary)
            if labels.count(tokenizer.eos_token_id) != 1:
                raise ValueError("EOS was not supervised exactly once")

    def evaluate(stage):
        loss = trainer.evaluate()["eval_loss"]
        if not math.isfinite(loss):
            raise ValueError("Non-finite validation loss")
        FastLanguageModel.for_inference(model)
        outputs = []
        for row in generation:
            pair = render_prompt_completion(tokenizer, row)
            inputs = tokenizer(pair["prompt"], return_tensors="pt", add_special_tokens=False).to(
                "cuda"
            )
            with torch.inference_mode():
                ids = model.generate(
                    **inputs,
                    do_sample=False,
                    max_new_tokens=512,
                    eos_token_id=tokenizer.eos_token_id,
                    pad_token_id=tokenizer.pad_token_id,
                )[0, inputs.input_ids.shape[1] :].tolist()
            outputs.append(
                {
                    "record_id": row["record_id"],
                    "generated_token_ids": ids,
                    "output": tokenizer.decode(ids, skip_special_tokens=True),
                }
            )
        (a.output / f"{stage}.json").write_text(
            json.dumps(
                {"mean_example_response_nll": loss, "records": outputs},
                ensure_ascii=False,
                indent=2,
            )
            + "\n"
        )
        FastLanguageModel.for_training(model, use_gradient_checkpointing="unsloth")

    evaluate("base")
    trainer.train()
    checkpoint = a.output / "trainer" / f"checkpoint-{trainer.state.global_step}"
    hashes = require_complete_checkpoint(checkpoint, trainer.state.global_step)
    if trainer.accelerator.scaler is not None and not (checkpoint / "scaler.pt").is_file():
        raise ValueError("Mixed-precision scaler checkpoint is missing")
    changed = 0
    for key, value in get_peft_model_state_dict(model).items():
        if not torch.isfinite(value).all():
            raise ValueError("Non-finite trained adapter")
        changed += not torch.equal(value.detach().cpu(), initial_adapter[key])
    if not changed:
        raise ValueError("No adapter tensor changed")

    # Checkpoints at intermediate steps remain available for paired offline evaluation.
    evaluate("pilot_end")
    exported = deepcopy(tokenizer)
    exported.chat_template = native_eos_template(tokenizer.chat_template)
    exported.save_pretrained(str(a.output / "inference-tokenizer"))
    summary = {
        "status": "pilot_completed_pending_quality_review",
        "steps": trainer.state.global_step,
        "changed_adapter_tensors": changed,
        "checkpoint": str(checkpoint),
        "checkpoint_hashes": hashes,
        "configuration": cfg,
        "script_sha256": sha256(Path(__file__)),
        "test_records_used": 0,
        "automatic_full_training": False,
        "limits": [
            "Intermediate checkpoint evaluation and CUDA resume/reload equivalence still required."
        ],
    }
    (a.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    main()
