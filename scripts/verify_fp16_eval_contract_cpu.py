#!/usr/bin/env python3
"""Reproduce the AMP gradient contract independently of the GPU training stack."""

import argparse
import json
from pathlib import Path

import torch


def trial(full_eval_cast):
    torch.manual_seed(42)
    model = torch.nn.Linear(2, 1, bias=False)
    with torch.no_grad():
        model.weight.fill_(0.125)
    if full_eval_cast:
        model.to(dtype=torch.float16)
    before = model.weight.detach().clone()
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.001)
    scaler = torch.amp.GradScaler("cpu", init_scale=128.0)
    with torch.autocast("cpu", dtype=torch.float16):
        loss = model(torch.ones(2, 2)).square().mean()
    scaler.scale(loss).backward()
    error = None
    try:
        scaler.step(optimizer)
        scaler.update()
    except ValueError as exc:
        error = str(exc)
    return {
        "full_eval_cast": full_eval_cast,
        "parameter_dtype": str(model.weight.dtype),
        "gradient_dtype": str(model.weight.grad.dtype),
        "error": error,
        "weights_changed": not torch.equal(before, model.weight.detach()),
        "weights_finite": bool(torch.isfinite(model.weight).all()),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    broken, corrected = trial(True), trial(False)
    assert broken["error"] == "Attempting to unscale FP16 gradients."
    assert not broken["weights_changed"]
    assert corrected["error"] is None
    assert corrected["weights_changed"] and corrected["weights_finite"]
    report = {
        "status": "cpu_amp_contract_verified",
        "torch_version": torch.__version__,
        "device": "cpu",
        "before": broken,
        "after": corrected,
        "limit": "Tiny linear model; does not prove Unsloth CUDA training or clinical quality.",
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
