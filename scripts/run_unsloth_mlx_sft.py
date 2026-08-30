#!/usr/bin/env python3
"""Run the governed synthetic SFT micro-run with Unsloth Core on Apple MLX."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from triage_poc.sft_dataset import SftDatasetError, render_sft_dataset
from triage_poc.training_preflight import require_approved_manifests

TARGET_MODULES = (
    "q_proj",
    "k_proj",
    "v_proj",
    "o_proj",
    "gate_proj",
    "up_proj",
    "down_proj",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-steps", type=int, default=20)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def load_split(input_path: Path, split: str) -> list[dict[str, object]]:
    records = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise SftDatasetError("The canonical input must contain a JSON array.")
    selected = [record for record in records if record.get("split") == split]
    if not selected:
        raise SftDatasetError(f"No records found for split '{split}'.")
    return render_sft_dataset(selected)


def main() -> int:
    args = parse_args()
    manifest_directory = Path(__file__).resolve().parents[1] / "data" / "manifests"
    require_approved_manifests(manifest_directory, [args.manifest])
    if not args.model_path.is_dir():
        raise FileNotFoundError(f"Model snapshot not found: {args.model_path}")
    if args.max_steps <= 0:
        raise ValueError("--max-steps must be positive.")

    train_records = load_split(args.input, "train")
    validation_records = load_split(args.input, "validation")
    print(
        "Core MLX preflight passed: "
        f"train={len(train_records)}, validation={len(validation_records)}, "
        "model=Qwen3-1.7B-Base, chat_template=qwen3."
    )
    if args.dry_run:
        return 0

    from datasets import Dataset
    from unsloth import FastLanguageModel
    from unsloth_zoo.mlx.trainer import MLXTrainer, MLXTrainingConfig

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=str(args.model_path),
        max_seq_length=2048,
        load_in_4bit=True,
        chat_template="qwen3",
        random_state=42,
    )
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        target_modules=list(TARGET_MODULES),
        lora_alpha=16,
        lora_dropout=0,
        use_rslora=False,
        random_state=42,
        max_seq_length=2048,
    )
    training_args = MLXTrainingConfig(
        output_dir=str(args.output_dir),
        max_steps=args.max_steps,
        # The governed synthetic micro-fixture intentionally has one train row.
        # Keep an effective batch of eight without duplicating that example.
        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=8,
        learning_rate=2e-4,
        warmup_steps=3,
        seed=42,
        logging_steps=1,
        eval_steps=1,
        save_steps=0,
        report_to="none",
        max_seq_length=2048,
        chat_template="qwen3",
        train_on_completions=False,
        completion_only_loss=False,
    )
    trainer = MLXTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=Dataset.from_list(train_records),
        eval_dataset=Dataset.from_list(validation_records),
        args=training_args,
    )
    result = trainer.train()
    trainer.save_model(str(args.output_dir))
    summary = {
        "base_model_snapshot": str(args.model_path),
        "chat_template": "qwen3",
        "data_origin": "synthetic",
        "manifest": args.manifest,
        "max_steps": args.max_steps,
        "train_records": len(train_records),
        "validation_records": len(validation_records),
        "per_device_train_batch_size": 1,
        "gradient_accumulation_steps": 8,
        "train_metrics": getattr(result, "metrics", {}),
    }
    (args.output_dir / "run_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Saved LoRA adapters to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
