"""Fail-closed budget and checkpoint contracts for the source SFT pilot."""

import hashlib
import json
import time
from pathlib import Path


def validate_pilot_config(config: dict) -> None:
    if config["initial_checkpoint"] != "base_only_no_v5_adapter":
        raise ValueError("The pilot must start from the pinned base")
    if not config["completion_only_loss"] or config["packing"] or config["test_records_used"]:
        raise ValueError("Invalid pilot data/loss contract")
    if not 0 < config["pilot_stop_after_steps"] < config["scheduler_horizon_steps"]:
        raise ValueError("Pilot must stop before the fixed scheduler horizon")
    if not 0 < config["pilot_training_wall_seconds"] <= 1800:
        raise ValueError("Training budget must not exceed 30 minutes")
    if config["save_only_model"] or config["decision"]["automatic_full_training"]:
        raise ValueError("Resumable checkpoints and manual continuation decision required")


def require_complete_checkpoint(path: Path, step: int) -> dict:
    required = [
        "adapter_model.safetensors",
        "optimizer.pt",
        "scheduler.pt",
        "rng_state.pth",
        "trainer_state.json",
    ]
    if any(not (path / f).is_file() or not (path / f).stat().st_size for f in required):
        raise ValueError("Incomplete resumable checkpoint")
    state = json.loads((path / "trainer_state.json").read_text())
    if state["global_step"] != step:
        raise ValueError("Checkpoint step mismatch")
    return {f: hashlib.sha256((path / f).read_bytes()).hexdigest() for f in required}


class PilotBudget:
    """Stop at an optimizer-step boundary and request an ordinary full checkpoint."""

    def __init__(self, max_steps: int, seconds: float, clock=time.monotonic):
        self.max_steps = max_steps
        self.seconds = seconds
        self.clock = clock
        self.started = None

    def start(self):
        self.started = self.clock()

    def reached(self, step: int) -> bool:
        if self.started is None:
            raise ValueError("Budget clock has not started")
        return step >= self.max_steps or self.clock() - self.started >= self.seconds
