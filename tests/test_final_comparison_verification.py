"""Check saved final measurements using only synthetic generated artifacts."""

import json
import runpy
from pathlib import Path

import pytest

from triage_poc.comparison import sha256
from triage_poc.final_selection import select_generation_ids

verify = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "scripts/verify_final_comparison.py")
)["verify"]


def test_final_verification_recomputes_and_rejects_corruption(tmp_path):
    def write(path, value):
        path.write_text(json.dumps(value))

    rows = [
        {
            "record_id": f"synthetic-{i}",
            "messages": [
                {"role": role, "content": "synthetic"} for role in ("system", "user", "assistant")
            ],
        }
        for i in range(500)
    ]
    test = tmp_path / "test.jsonl"
    test.write_text("\n".join(json.dumps(row) for row in rows))
    hashes = dict.fromkeys(["runner", "sft_manifest", "data_manifest", "dpo_summary"], "a" * 64)
    hashes["test"] = sha256(test)
    versions = dict.fromkeys(["torch", "transformers", "peft", "bitsandbytes"], "1.0")
    freeze = {
        "status": "frozen",
        "split": "test",
        "expected_examples": 500,
        "generation_examples": 50,
        "selection_seed": 42,
        "max_new_tokens": 512,
        "do_sample": False,
        "optimizer_steps": 0,
        "variants": ["base", "sft", "dpo"],
        "input_hashes": hashes,
        "package_versions": versions,
    }
    freeze_path = tmp_path / "freeze.json"
    write(freeze_path, freeze)
    run = tmp_path / "run"
    run.mkdir()
    write(run / "final_freeze.json", freeze)
    selected = select_generation_ids(row["record_id"] for row in rows)
    write(run / "selected_ids.json", selected)
    metric = {
        "mean_example_response_nll": 1.0,
        "loss_records": 500,
        "qa_eos_terminated": 50,
        "triage": None,
    }
    summary = {
        "status": "completed",
        "evaluation_split": "test",
        "test_records_used": 500,
        "optimizer_steps": 0,
        "input_hashes": {**hashes, "final_freeze": sha256(freeze_path)},
        "script_sha256": hashes["runner"],
        "package_versions": versions,
        "dpo_artifact": {"run_summary_sha256": hashes["dpo_summary"]},
        "comparison": dict.fromkeys(["base", "sft", "dpo"], metric),
    }
    write(run / "summary.json", summary)
    data = {
        "losses": [{"record_id": row["record_id"], "response_nll": 1.0} for row in rows],
        "qa": [
            {
                "record_id": identifier,
                "eos_terminated": True,
                "output": "synthetic",
                "generated_token_ids": [42],
                "latency_ms": 1.0,
            }
            for identifier in selected
        ],
        "triage": [],
    }
    for stage in ("base", "sft", "dpo"):
        write(run / f"{stage}.json", data)
    assert verify(run, test, freeze_path)["status"] == "final_saved_metrics_recomputed"
    data["losses"][0]["response_nll"] = 2.0
    write(run / "dpo.json", data)
    with pytest.raises(ValueError, match="differs"):
        verify(run, test, freeze_path)
    data["losses"][0]["response_nll"] = 1.0
    data["qa"].pop()
    write(run / "dpo.json", data)
    with pytest.raises(ValueError, match="population"):
        verify(run, test, freeze_path)
