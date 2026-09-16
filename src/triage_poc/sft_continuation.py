"""Validate a bounded continuation of the verified general pilot."""

import json

from triage_poc.comparison import sha256
from triage_poc.sft_pilot import require_complete_checkpoint


def validate_continuation(checkpoint, config, plan):
    if plan["start_step"] != 150 or plan["stop_step"] != 500 or plan["training_seconds"] != 1800:
        raise ValueError("Only the authorized 150-to-500 continuation is allowed")
    source = checkpoint.parent.parent / "summary.json"
    if sha256(source) != plan["source_summary_sha256"]:
        raise ValueError("Wrong source pilot summary")
    prior = json.loads(source.read_text())
    if prior["configuration"] != config or prior["mode"] != "pilot" or prior["steps"] != 150:
        raise ValueError("Continuation requires the unchanged general pilot")
    hashes = require_complete_checkpoint(checkpoint, 150)
    if hashes != prior["checkpoint_hashes"] or hashes != plan["checkpoint_hashes"]:
        raise ValueError("Continuation checkpoint hashes changed")
    if sha256(checkpoint / "scaler.pt") != plan["scaler_sha256"]:
        raise ValueError("AMP scaler changed")
    return hashes
