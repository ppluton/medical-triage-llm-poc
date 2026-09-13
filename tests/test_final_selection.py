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
