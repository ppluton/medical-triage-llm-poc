#!/usr/bin/env python3
"""Verify real TRL labels and resumable PEFT training on a tiny synthetic CPU model."""

import argparse
import json
from pathlib import Path

import torch
from datasets import Dataset, disable_progress_bars
from peft import LoraConfig, get_peft_model, get_peft_model_state_dict
from transformers import AutoTokenizer, Qwen3Config, Qwen3ForCausalLM, TrainerCallback, set_seed
from trl import SFTConfig, SFTTrainer

from triage_poc.comparison import sha256
from triage_poc.sft_termination import render_prompt_completion, validate_completion_labels


class StopAtTwo(TrainerCallback):
    def on_step_end(self, args, state, control, **kwargs):
        if state.global_step == 2:
            control.should_save = True
            control.should_training_stop = True
        return control


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--tokenizer", type=Path, required=True)
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError("Fresh proof output required")
    a.output.mkdir(parents=True)
    torch.set_num_threads(1)
    disable_progress_bars()
    tokenizer = AutoTokenizer.from_pretrained(str(a.tokenizer), local_files_only=True)

    def model():
        set_seed(321)
        m = Qwen3ForCausalLM(
            Qwen3Config(
                vocab_size=len(tokenizer),
                hidden_size=16,
                intermediate_size=32,
                num_hidden_layers=1,
                num_attention_heads=2,
                num_key_value_heads=1,
                head_dim=8,
                max_position_embeddings=2048,
                attention_dropout=0.0,
                attn_implementation="eager",
            )
        )
        return get_peft_model(
            m,
            LoraConfig(
                r=2,
                lora_alpha=2,
                lora_dropout=0,
                target_modules=["q_proj", "v_proj"],
                task_type="CAUSAL_LM",
            ),
        )

    def trainer(name, dataset, callbacks=None):
        return SFTTrainer(
            model=model(),
            processing_class=tokenizer,
            train_dataset=dataset,
            args=SFTConfig(
                output_dir=str(a.output / name),
                max_steps=4,
                per_device_train_batch_size=1,
                gradient_accumulation_steps=2,
                learning_rate=0.001,
                warmup_steps=1,
                lr_scheduler_type="linear",
                optim="adamw_torch",
                use_cpu=True,
                bf16=False,
                fp16=False,
                gradient_checkpointing=False,
                seed=321,
                data_seed=321,
                save_strategy="steps",
                save_steps=2,
                save_only_model=False,
                logging_steps=1,
                report_to="none",
                max_length=2048,
                completion_only_loss=True,
                packing=False,
                padding_free=False,
                dataset_num_proc=1,
                dataloader_num_workers=0,
                disable_tqdm=True,
            ),
            callbacks=callbacks,
        )

    rows = []
    for name in ("train-qwen3.jsonl", "validation-qwen3.jsonl"):
        rows.extend(json.loads(line) for line in (a.data / name).read_text().splitlines())
    pairs = [render_prompt_completion(tokenizer, row) for row in rows]
    audit_trainer = trainer("labels-only", Dataset.from_list(pairs))
    for i, pair in enumerate(pairs):
        example = audit_trainer.train_dataset[i]
        full = tokenizer.encode(pair["prompt"] + pair["completion"], add_special_tokens=False)
        boundary = len(tokenizer.encode(pair["prompt"], add_special_tokens=False))
        assert example["input_ids"] == full
        labels = audit_trainer.data_collator([example])["labels"].flatten().tolist()
        validate_completion_labels(labels, full, boundary)
        assert labels.count(tokenizer.eos_token_id) == 1
    del audit_trainer
    synthetic = Dataset.from_list(
        [
            render_prompt_completion(
                tokenizer,
                {
                    "record_id": f"synthetic-{i}",
                    "messages": [
                        {"role": "system", "content": "Synthetic token test."},
                        {"role": "user", "content": f"Return symbol alpha for test {i}."},
                        {"role": "assistant", "content": "alpha"},
                    ],
                },
            )
            for i in range(8)
        ]
    )
    uninterrupted = trainer("continuous", synthetic)
    uninterrupted.train()
    expected = {
        k: v.detach().clone() for k, v in get_peft_model_state_dict(uninterrupted.model).items()
    }
    del uninterrupted
    interrupted = trainer("interrupted", synthetic, [StopAtTwo()])
    interrupted.train()
    assert interrupted.state.global_step == 2
    checkpoint = a.output / "interrupted/checkpoint-2"
    required = [
        "adapter_model.safetensors",
        "optimizer.pt",
        "scheduler.pt",
        "rng_state.pth",
        "trainer_state.json",
    ]
    assert all((checkpoint / f).is_file() and (checkpoint / f).stat().st_size for f in required)
    del interrupted
    resumed = trainer("resumed", synthetic)
    resumed.train(resume_from_checkpoint=str(checkpoint))
    assert resumed.state.global_step == 4
    actual = get_peft_model_state_dict(resumed.model)
    assert set(expected) == set(actual)
    assert all(torch.equal(expected[k], actual[k]) for k in expected)
    import importlib.metadata as metadata

    report = {
        "status": "passed",
        "environment": "local_cpu_tiny_random_model",
        "actual_trl_label_records": len(rows),
        "supervised_prompt_tokens": 0,
        "all_response_tokens_supervised": True,
        "native_eos_per_record": 1,
        "synthetic_training_only": True,
        "medical_training_steps": 0,
        "resume": {
            "continuous_steps": 4,
            "interrupted_at": 2,
            "resumed_to": 4,
            "adapter_tensors_bitwise_equal": True,
            "required_files": required,
        },
        "versions": {
            k: metadata.version(k)
            for k in ["torch", "transformers", "trl", "peft", "datasets", "accelerate"]
        },
        "script_sha256": sha256(Path(__file__)),
        "limits": ["CPU proof does not cover CUDA quantization, Unsloth or fp16 scaler resume."],
    }
    (a.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
