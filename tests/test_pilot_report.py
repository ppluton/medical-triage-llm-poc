import copy

import pytest

from triage_poc.pilot_report import summarize_pilot


def fixture():
    cfg = {"evaluation": {"generation_record_ids": ["v"], "max_new_tokens": 8}}
    refs = {
        "v": {
            "split": "validation",
            "response": "Synthetic alpha.",
            "source": {"source_dataset": "synthetic"},
        }
    }
    before = {
        "mean_example_response_nll": 2.0,
        "records": [{"record_id": "v", "output": "loop", "generated_token_ids": [1] * 8}],
    }
    after = {
        "mean_example_response_nll": 1.0,
        "records": [
            {"record_id": "v", "output": "Synthetic alpha", "generated_token_ids": [2, 151643]}
        ],
    }
    return cfg, {"base": before, "pilot_end": after}, refs


def test_paired_improvement_does_not_approve_full_training():
    cfg, stages, refs = fixture()
    report = summarize_pilot(cfg, stages, refs)
    assert report["response_nll_delta"] == -1
    assert report["stages"]["pilot_end"]["native_eos_terminated"] == 1
    assert report["stages"]["pilot_end"]["exact_normalized_reference_matches"] == 1
    assert report["stages"]["base"]["by_source"]["synthetic"]["reached_token_cap"] == 1
    assert report["stages"]["pilot_end"]["by_source"]["synthetic"]["native_eos_terminated"] == 1
    assert report["full_training_approved"] is False


def test_rejects_incomparable_or_test_records():
    cfg, stages, refs = fixture()
    bad = copy.deepcopy(stages)
    bad["pilot_end"]["records"] = []
    with pytest.raises(ValueError, match="frozen IDs"):
        summarize_pilot(cfg, bad, refs)
    refs["v"]["split"] = "test"
    with pytest.raises(ValueError, match="validation"):
        summarize_pilot(cfg, stages, refs)


def test_terminated_empty_output_is_not_treated_as_an_answer():
    cfg, stages, refs = fixture()
    stages["base"]["records"][0].update(output=" \n", generated_token_ids=[12, 151643])
    report = summarize_pilot(cfg, stages, refs)
    base = report["stages"]["base"]
    assert base["native_eos_terminated"] == 1
    assert base["empty_outputs"] == 1
    assert base["exact_normalized_reference_matches"] == 0
    assert base["by_source"]["synthetic"]["empty_outputs"] == 1
