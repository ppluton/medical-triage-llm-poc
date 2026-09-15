from copy import deepcopy

import pytest

from triage_poc.termination_report import summarize_termination_run


def fixture():
    summary = {"status": "completed", "test_records_used": 0,
        "training_args": {"max_steps": 20}, "changed_adapter_tensors": 4,
        "validation_ids": ["synthetic-a"]}
    row = {"record_id": "synthetic-a", "generated_token_ids": [1, 2, 151643],
           "generated_tokens": 3}
    return summary, {stage: [deepcopy(row)] for stage in ("before", "after", "reloaded")}


def test_reload_and_termination_are_separate_from_full_training_approval():
    summary, stages = fixture()
    result = summarize_termination_run(summary, stages)
    assert result["status"] == "termination_smoke_passed"
    assert result["reload_tokens_identical"] is True
    assert result["full_training_approved"] is False


def test_repeated_cap_is_a_failed_generation_gate_even_when_reload_matches():
    summary, stages = fixture()
    for stage in ("after", "reloaded"):
        stages[stage][0].update(generated_token_ids=[1] * 256, generated_tokens=256)
    result = summarize_termination_run(summary, stages)
    assert result["status"] == "generation_gate_failed"
    assert result["stages"]["after"]["mean_repeated_token_4gram_fraction"] > 0.99


def test_rejects_reload_drift_and_missing_records():
    summary, stages = fixture()
    stages["reloaded"][0]["generated_token_ids"][0] = 99
    with pytest.raises(ValueError, match="Reloaded generations differ"):
        summarize_termination_run(summary, stages)
    stages["reloaded"] = []
    with pytest.raises(ValueError, match="same validation IDs"):
        summarize_termination_run(summary, stages)
