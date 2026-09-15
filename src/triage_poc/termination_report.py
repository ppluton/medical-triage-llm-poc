"""Summarize bounded generation checks without clinical quality claims."""
from __future__ import annotations

from collections import Counter


def summarize_termination_run(summary: dict, stages: dict[str, list[dict]]) -> dict:
    if summary.get("status") != "completed" or summary.get("test_records_used") != 0:
        raise ValueError("A completed, test-free experiment is required")
    if summary.get("training_args", {}).get("max_steps") != 20:
        raise ValueError("Expected the bounded 20-step experiment")
    if summary.get("changed_adapter_tensors", 0) <= 0:
        raise ValueError("No changed adapter tensors recorded")
    expected = summary["validation_ids"]
    if not expected or len(set(expected)) != len(expected):
        raise ValueError("Invalid validation IDs")
    reports = {}
    indexed = {}
    for stage in ("before", "after", "reloaded"):
        rows = stages[stage]
        by_id = {row["record_id"]: row for row in rows}
        if len(rows) != len(by_id) or set(by_id) != set(expected):
            raise ValueError("Generation records do not cover the same validation IDs")
        indexed[stage] = by_id
        lengths, repeats = [], []
        terminated = 0
        for row in rows:
            ids = row["generated_token_ids"]
            if not ids or len(ids) != row["generated_tokens"]:
                raise ValueError("Generated token count is inconsistent")
            if len(ids) > 256:
                raise ValueError("Generation exceeded the experiment cap")
            lengths.append(len(ids))
            terminated += ids[-1] in (151643, 151645)
            grams = Counter(tuple(ids[i:i + 4]) for i in range(len(ids) - 3))
            repeats.append(sum(n - 1 for n in grams.values()) / max(1, sum(grams.values())))
        reports[stage] = {"records": len(rows), "token_lengths": lengths,
            "terminated_with_eos": terminated, "reached_256_tokens": lengths.count(256),
            "mean_repeated_token_4gram_fraction": sum(repeats) / len(repeats)}
    identical = all(indexed["after"][key]["generated_token_ids"] ==
                    indexed["reloaded"][key]["generated_token_ids"] for key in expected)
    if not identical:
        raise ValueError("Reloaded generations differ from the saved model outputs")
    terminates = reports["after"]["terminated_with_eos"] == len(expected)
    return {"status": "termination_smoke_passed" if terminates else "generation_gate_failed",
        "dataset_version": summary.get("dataset_version", "v1"),
        "loss_scope": summary.get("loss_scope", "full"),
        "training_steps": 20, "changed_adapter_tensors": summary["changed_adapter_tensors"],
        "reload_tokens_identical": identical, "stages": reports,
        "test_records_used": 0, "full_training_approved": False,
        "limits": ["Three development examples only; inspect response content separately.",
                   "A short continuation does not establish full-corpus training readiness.",
                   "No clinical evaluation or DPO acceptance is established."]}
