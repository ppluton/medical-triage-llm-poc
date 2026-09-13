"""Verify deterministic selection without loading the reserved dataset."""

import pytest

from triage_poc.final_selection import select_generation_ids


def test_selection_is_independent_of_input_order_and_rng():
    identifiers = [f"synthetic-{index}" for index in range(500)]
    selected = select_generation_ids(identifiers)
    assert len(selected) == len(set(selected)) == 50
    assert set(selected) <= set(identifiers)
    assert selected == select_generation_ids(reversed(identifiers))
    assert selected != select_generation_ids(identifiers, seed=43)
    assert select_generation_ids(identifiers, count=10) == selected[:10]


@pytest.mark.parametrize(
    "identifiers,count,seed",
    [
        (["a", "a"], 1, 42),
        ([""], 1, 42),
        ([None], 1, 42),
        (["a"], 2, 42),
        (["a"], 0, 42),
        (["a"], True, 42),
        (["a"], 1, "42"),
    ],
)
def test_invalid_selection_is_rejected(identifiers, count, seed):
    with pytest.raises(ValueError):
        select_generation_ids(identifiers, count=count, seed=seed)


def test_freeze_rejects_proposals_and_changed_inputs():
    from triage_poc.final_selection import validate_final_freeze

    hashes = {"test": "a" * 64, "runner": "b" * 64}
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
        "package_versions": dict.fromkeys(["torch", "transformers", "peft", "bitsandbytes"], "1.0"),
    }
    validate_final_freeze(freeze, hashes)
    for change in (
        {"status": "proposed"},
        {"generation_examples": 30},
        {"package_versions": {}},
        {"input_hashes": {"test": "changed"}},
    ):
        with pytest.raises(ValueError):
            validate_final_freeze({**freeze, **change}, hashes)
