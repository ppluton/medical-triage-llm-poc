#!/usr/bin/env python3
"""Run a governed source-derived SFT LoRA micro-run with Unsloth Core/MLX."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import random
from collections import Counter
from pathlib import Path

from triage_poc.source_sft_preflight import (
    preflight_failures,
    rendered_token_summary,
    validate_source_sft_artifacts,
)

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
    parser.add_argument("--model-path", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--artifact-directory", required=True, type=Path)
    parser.add_argument("--output-directory", required=True, type=Path)
    parser.add_argument("--max-steps", type=int, default=20)
    parser.add_argument("--validation-sample-size", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def stable_validation_sample(
    rows: list[dict[str, object]], size: int, seed: int
) -> list[dict[str, object]]:
    if size <= 0 or size > len(rows):
        raise ValueError("Validation sample size must be between 1 and its split size.")
    return sorted(
        rows,
        key=lambda row: hashlib.sha256(
            f"{seed}:{row['record_id']}".encode()
        ).hexdigest(),
    )[:size]


def main() -> int:
    args = parse_args()
    if not 1 <= args.max_steps <= 20:
        raise ValueError("This micro-run is limited to 1–20 steps; "
                         "full training needs readiness evidence.")
    if not args.model_path.is_dir():
        raise FileNotFoundError(f"Model snapshot not found: {args.model_path}.")
    manifest, canonical, train, validation = validate_source_sft_artifacts(
        args.manifest, args.artifact_directory
    )
    validation_sample = stable_validation_sample(
        validation, args.validation_sample_size, args.seed
    )
    shuffled_train = list(train)
    random.Random(args.seed).shuffle(shuffled_train)
    canonical_by_id = {row["record_id"]: row for row in canonical}
    validation_sources = Counter(
        canonical_by_id[row["record_id"]]["source"]["source_dataset"]
        for row in validation_sample
    )
    print(
        "Source SFT MLX artifact checks passed (tokenizer audit pending): "
        f"train={len(train)}, validation_sample={len(validation_sample)}, "
        f"sources={dict(sorted(validation_sources.items()))}."
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
        random_state=args.seed,
    )
    failures = preflight_failures({split: rendered_token_summary(rows, tokenizer,
        max_sequence_length=2048)
        for split, rows in (("train", train), ("validation", validation))})
    if failures:
        raise ValueError("Training format preflight failed: " + "; ".join(failures))
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        target_modules=list(TARGET_MODULES),
        lora_alpha=16,
        lora_dropout=0,
        use_rslora=False,
        random_state=args.seed,
        max_seq_length=2048,
    )
    training_args = MLXTrainingConfig(
        output_dir=str(args.output_directory),
        max_steps=args.max_steps,
        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=8,
        learning_rate=2e-4,
        warmup_steps=3,
        seed=args.seed,
        logging_steps=1,
        eval_steps=5,
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
        train_dataset=Dataset.from_list(shuffled_train),
        eval_dataset=Dataset.from_list(validation_sample),
        args=training_args,
    )
    result = trainer.train()
    trainer.save_model(str(args.output_directory))
    summary = {
        "status": "completed_technical_micro_run",
        "base_model_snapshot": args.model_path.name,
        "chat_template": "qwen3",
        "dataset_manifest_id": manifest["manifest_id"],
        "dataset_sha256": manifest["artifacts"]["canonical"]["sha256"],
        "data_origin": "source_derived",
        "seed": args.seed,
        "max_steps": args.max_steps,
        "train_records_available": len(train),
        "validation_records_available": len(validation),
        "validation_records_used": len(validation_sample),
        "validation_source_counts": dict(sorted(validation_sources.items())),
        "test_records_used": 0,
        "per_device_train_batch_size": 1,
        "gradient_accumulation_steps": 8,
        "package_versions": {
            name: importlib.metadata.version(name)
            for name in ("unsloth", "unsloth-zoo", "datasets", "transformers")
        },
        "train_metrics": getattr(result, "metrics", {}),
        "limits": [
            "A 20-step micro-run proves pipeline execution, not convergence or quality gain.",
            "Only a deterministic 50-record validation sample is evaluated in this smoke run.",
            "No clinical validation was performed.",
        ],
    }
    args.output_directory.mkdir(parents=True, exist_ok=True)
    (args.output_directory / "run_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Saved source SFT LoRA micro-run to {args.output_directory}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
