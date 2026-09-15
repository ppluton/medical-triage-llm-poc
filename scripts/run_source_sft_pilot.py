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
    p.add_argument("--mechanics-smoke", action="store_true")
    p.add_argument("--resume-smoke-from", type=Path)
    p.add_argument("--verify-pilot-from", type=Path)
    p.add_argument("--memorization-manifest", type=Path)
    p.add_argument("--continue-pilot-from", type=Path)
    p.add_argument("--continuation-plan", type=Path)
    a = p.parse_args()
    if bool(a.continue_pilot_from) != bool(a.continuation_plan):
        p.error("Continuation checkpoint and plan must be provided together")
    if a.continue_pilot_from and (
        a.memorization_manifest or a.mechanics_smoke or a.resume_smoke_from or a.verify_pilot_from
    ):
        p.error("Continuation must not use diagnostic or reload modes")
    if a.memorization_manifest and (
        a.mechanics_smoke or a.resume_smoke_from or a.verify_pilot_from
    ):
        p.error("Memorization is separate from pilot and reload modes")
    if a.verify_pilot_from and (a.mechanics_smoke or a.resume_smoke_from):
        p.error("Pilot reload verification is read-only and separate from smoke training")
    if a.resume_smoke_from and not a.mechanics_smoke:
        p.error("Resume is restricted to the bounded mechanics smoke")
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
    continuation = None
    if a.continue_pilot_from:
        from triage_poc.sft_continuation import validate_continuation

        continuation = json.loads(a.continuation_plan.read_text())
        if sha256(a.config) != continuation["parent_config_sha256"]:
            raise ValueError("Continuation configuration changed")
        validate_continuation(a.continue_pilot_from, cfg, continuation)
    memorization = None
    if a.memorization_manifest:
        from triage_poc.memorization import select_memorization_rows

        memorization = json.loads(a.memorization_manifest.read_text())
        if memorization["parent_config_sha256"] != sha256(a.config):
            raise ValueError("Memorization parent configuration changed")
        train = select_memorization_rows(train, validation, memorization)
        # Deliberately measure the training cohort, never held-out quality.
        validation = deepcopy(train)
        generation = deepcopy(train)
        cfg = deepcopy(cfg)
        cfg.update(
            learning_rate=2e-4,
            warmup_steps=5,
            scheduler_horizon_steps=300,
            pilot_stop_after_steps=300,
            pilot_training_wall_seconds=900,
            gradient_accumulation_steps=1,
            save_steps=100,
        )
        cfg["training_records"] = 12
        cfg["validation_records"] = 0
        cfg["experiment_id"] = "train-only-memorization-12"
        cfg["evaluation"] = {
            "scope": "training_memorization_only",
            "loss_records": 12,
            "generation_records": 12,
            "max_new_tokens": 256,
        }

    if a.output.exists():
        raise ValueError("Fresh output required; continuation is a separate reviewed operation")
    if not a.execute_pilot:
        print(
            json.dumps(
                {
                    "status": "preflight_passed_not_launched",
                    "train": len(train),
                    "validation": 0 if memorization else len(validation),
                    "in_sample_evaluation_records": 12 if memorization else 0,
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
    stop_step = (
        (4 if a.resume_smoke_from else 2) if a.mechanics_smoke else cfg["pilot_stop_after_steps"]
    )
    if continuation:
        stop_step = continuation["stop_step"]
    budget = PilotBudget(
        stop_step, 180 if a.mechanics_smoke else cfg["pilot_training_wall_seconds"]
    )
    precision_events = []

    def check_precision(stage):
        counts = {}
        for name, parameter in model.named_parameters():
            if parameter.requires_grad:
                counts[str(parameter.dtype)] = counts.get(str(parameter.dtype), 0) + 1
                if parameter.dtype != torch.float32:
                    raise ValueError(f"Trainable parameter lost FP32 precision at {stage}: {name}")
        if not counts:
            raise ValueError("No trainable parameters")
        event = {"stage": stage, "trainable_tensor_dtypes": counts}
        precision_events.append(event)
        print(json.dumps(event), flush=True)

    class BoundedTraining(TrainerCallback):
        def on_train_begin(self, args, state, control, **kwargs):
            budget.start()
            if a.resume_smoke_from or continuation:
                optimizer = kwargs["optimizer"]
                saved_steps = {int(v["step"]) for v in optimizer.state.values() if "step" in v}
                expected_step = 150 if continuation else 2
                if state.global_step != expected_step or saved_steps != {expected_step}:
                    raise ValueError("Resume did not restore optimizer steps")
                if continuation:
                    restored_scheduler = kwargs["lr_scheduler"].state_dict()
                    saved_scheduler = torch.load(
                        a.continue_pilot_from / "scheduler.pt",
                        map_location="cpu",
                        weights_only=True,
                    )
                    saved_scaler = torch.load(
                        a.continue_pilot_from / "scaler.pt", map_location="cpu", weights_only=True
                    )
                    if (
                        restored_scheduler != saved_scheduler
                        or restored_scheduler["last_epoch"] != 150
                    ):
                        raise ValueError("Scheduler was not restored exactly")
                    if [g["lr"] for g in optimizer.param_groups] != saved_scheduler["_last_lr"]:
                        raise ValueError("Optimizer learning rates were not restored")
                    if (
                        trainer.accelerator.scaler.state_dict() != saved_scaler
                        or args.ignore_data_skip
                    ):
                        raise ValueError("Scaler or data-skip policy changed")
                    print(
                        json.dumps(
                            {
                                "stage": "continuation_scheduler_scaler_verified",
                                "scheduler_last_epoch": 150,
                                "learning_rates": saved_scheduler["_last_lr"],
                                "data_skip_enabled": True,
                            }
                        ),
                        flush=True,
                    )
                print(
                    json.dumps(
                        {
                            "stage": "optimizer_resume_verified",
                            "global_step": state.global_step,
                            "optimizer_steps": sorted(saved_steps),
                        }
                    ),
                    flush=True,
                )

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
        eval_dataset=Dataset.from_list(val_pairs[:2] if a.mechanics_smoke else val_pairs),
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
    # Unsloth overrides these flags in its constructor. Full-eval casting mutates
    # FP32 adapter storage before AMP training, so override after construction.
    trainer.args.fp16_full_eval = False
    trainer.args.bf16_full_eval = False
    check_precision("trainer_ready")
    if a.mechanics_smoke:
        generation = generation[:2]
    if a.resume_smoke_from or a.verify_pilot_from or continuation:
        from peft import set_peft_model_state_dict
        from safetensors.torch import load_file

        source_checkpoint = a.resume_smoke_from or a.verify_pilot_from or a.continue_pilot_from
        if a.verify_pilot_from:
            prior_summary = json.loads(
                (source_checkpoint.parent.parent / "summary.json").read_text()
            )
            if (
                prior_summary["configuration"] != cfg
                or prior_summary.get("mode") != "pilot"
                or prior_summary["steps"] != cfg["pilot_stop_after_steps"]
            ):
                raise ValueError("Reload source does not match the completed frozen pilot")
            verified_hashes = require_complete_checkpoint(source_checkpoint, prior_summary["steps"])
            if verified_hashes != prior_summary["checkpoint_hashes"]:
                raise ValueError("Pilot checkpoint hashes changed")
        elif continuation:
            require_complete_checkpoint(source_checkpoint, 150)
        else:
            require_complete_checkpoint(source_checkpoint, 2)
        if not (source_checkpoint / "scaler.pt").is_file():
            raise ValueError("Source checkpoint requires its AMP scaler")
        set_peft_model_state_dict(
            model, load_file(str(source_checkpoint / "adapter_model.safetensors"))
        )
    if continuation:
        initial_adapter = {
            k: v.detach().cpu().clone() for k, v in get_peft_model_state_dict(model).items()
        }
    for dataset, pairs in [(trainer.train_dataset, train_pairs), (trainer.eval_dataset, val_pairs)]:
        for i, pair in enumerate(pairs[: len(dataset)]):
            ids = tokenizer.encode(pair["prompt"] + pair["completion"], add_special_tokens=False)
            if dataset[i]["input_ids"] != ids:
                raise ValueError("Trainer tokenization changed")
            labels = trainer.data_collator([dataset[i]])["labels"].flatten().tolist()
            boundary = len(tokenizer.encode(pair["prompt"], add_special_tokens=False))
            validate_completion_labels(labels, ids, boundary)
            if labels.count(tokenizer.eos_token_id) != 1:
                raise ValueError("EOS was not supervised exactly once")

    def evaluate(stage):
        print(json.dumps({"stage": stage, "action": "evaluation_started"}), flush=True)
        check_precision(stage + "_before_evaluation")
        loss = trainer.evaluate()["eval_loss"]
        check_precision(stage + "_after_loss")
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
                    max_new_tokens=cfg["evaluation"]["max_new_tokens"],
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
        print(
            json.dumps(
                {
                    "stage": stage,
                    "action": "evaluation_completed",
                    "loss": loss,
                    "generated_tokens": [len(r["generated_token_ids"]) for r in outputs],
                }
            ),
            flush=True,
        )
        FastLanguageModel.for_training(model, use_gradient_checkpointing="unsloth")
        check_precision(stage + "_after_generation")

    print(
        json.dumps(
            {
                "stage": "all_labels_verified",
                "records": len(trainer.train_dataset) + len(trainer.eval_dataset),
            }
        ),
        flush=True,
    )
    if a.verify_pilot_from:
        evaluate("reloaded")
        previous = json.loads((a.verify_pilot_from.parent.parent / "pilot_end.json").read_text())
        reloaded = json.loads((a.output / "reloaded.json").read_text())
        if previous["records"] != reloaded["records"]:
            raise ValueError("Fresh-process pilot reload changed greedy generations")
        loss_delta = abs(
            previous["mean_example_response_nll"] - reloaded["mean_example_response_nll"]
        )
        if loss_delta > 1e-5:
            raise ValueError("Fresh-process pilot reload changed validation loss")
        intermediate_hashes = {}
        for step in (50, 100):
            candidate = a.verify_pilot_from.parent / f"checkpoint-{step}"
            intermediate_hashes[str(step)] = require_complete_checkpoint(candidate, step)
            set_peft_model_state_dict(
                model, load_file(str(candidate / "adapter_model.safetensors"))
            )
            evaluate(f"checkpoint_{step}")
        report = {
            "intermediate_checkpoint_hashes": intermediate_hashes,
            "intermediate_checkpoints_evaluated": [50, 100],
            "status": "pilot_fresh_reload_verified",
            "optimizer_steps_executed": 0,
            "identical_generations": len(generation),
            "loss_records": len(trainer.eval_dataset),
            "absolute_loss_delta": loss_delta,
            "checkpoint_hashes": verified_hashes,
            "configuration": cfg,
            "script_sha256": sha256(Path(__file__)),
            "precision_events": precision_events,
            "test_records_used": 0,
            "limits": ["Read-only reload; long training and clinical quality are not approved."],
        }
        (a.output / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report), flush=True)
        return
    evaluate("resume_start" if continuation else "base")
    if continuation:
        before = json.loads((a.continue_pilot_from.parent.parent / "pilot_end.json").read_text())
        reloaded = json.loads((a.output / "resume_start.json").read_text())
        if (
            before["records"] != reloaded["records"]
            or abs(before["mean_example_response_nll"] - reloaded["mean_example_response_nll"])
            > 1e-5
        ):
            raise ValueError("Checkpoint-150 reload changed before continuation")
        print(
            json.dumps(
                {"stage": "continuation_reload_verified", "identical_generations": len(generation)}
            ),
            flush=True,
        )
    if a.resume_smoke_from:
        previous = json.loads((a.resume_smoke_from.parent.parent / "pilot_end.json").read_text())
        reloaded = json.loads((a.output / "base.json").read_text())
        if previous["records"] != reloaded["records"]:
            raise ValueError("Fresh-process smoke reload changed greedy generations")
        print(
            json.dumps({"stage": "fresh_reload_verified", "records": len(generation)}), flush=True
        )
    resume_path = a.resume_smoke_from or a.continue_pilot_from
    trainer.train(resume_from_checkpoint=str(resume_path) if resume_path else None)
    if a.mechanics_smoke and trainer.state.global_step != stop_step:
        raise ValueError("Smoke failed to complete the required optimizer steps")
    check_precision("training_completed")
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
    memorization_result = None
    if memorization:
        from triage_poc.pilot_report import normalize_answer

        stages = {}
        expected = {r["record_id"]: r["messages"][-1]["content"] for r in train}
        for stage in ("base", "pilot_end"):
            records = json.loads((a.output / f"{stage}.json").read_text())["records"]
            stages[stage] = {
                "exact_answers": sum(
                    normalize_answer(r["output"]) == normalize_answer(expected[r["record_id"]])
                    for r in records
                ),
                "eos_terminated": sum(
                    r["generated_token_ids"][-1] == tokenizer.eos_token_id for r in records
                ),
                "records": len(records),
            }
        memorization_result = {
            "manifest": memorization,
            "stages": stages,
            "generalization_measured": False,
            "validation_records_used": 0,
        }
    summary = {
        "continuation": continuation,
        "optimizer_steps_executed": trainer.state.global_step
        - (150 if continuation else 2 if a.resume_smoke_from else 0),
        "memorization": memorization_result,
        "status": "memorization_completed"
        if memorization
        else "mechanics_smoke_completed"
        if a.mechanics_smoke
        else "pilot_completed_pending_quality_review",
        "mode": "general_pilot_continuation"
        if continuation
        else "training_memorization"
        if memorization
        else "resume_smoke"
        if a.resume_smoke_from
        else "mechanics_smoke"
        if a.mechanics_smoke
        else "pilot",
        "precision_events": precision_events,
        "resume_checkpoint": str(resume_path) if resume_path else None,
        "evaluated_records": len(trainer.eval_dataset),
        "generation_records": len(generation),
        "steps": trainer.state.global_step,
        "changed_adapter_tensors": changed,
        "checkpoint": str(checkpoint),
        "checkpoint_hashes": hashes,
        "configuration": cfg,
        "script_sha256": sha256(Path(__file__)),
        "test_records_used": 0,
        "automatic_full_training": False,
        "limits": [
            "Training memorization only, no held-out or clinical evaluation."
            if memorization
            else (
                "Intermediate checkpoint evaluation and CUDA "
                "resume/reload equivalence still required."
            )
        ],
    }
    (a.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    main()
