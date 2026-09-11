import pytest

from triage_poc.memorization import select_memorization_rows


def test_selection_preserves_frozen_order_and_rejects_held_out_ids():
    train = [{"record_id": str(i)} for i in range(14)]
    manifest = {"record_ids": [str(i) for i in reversed(range(12))]}
    assert [r["record_id"] for r in select_memorization_rows(train, [], manifest)] == manifest[
        "record_ids"
    ]
    with pytest.raises(ValueError, match="only use train"):
        select_memorization_rows(train, [{"record_id": "3"}], manifest)
    manifest["record_ids"][0] = "test-only"
    with pytest.raises(ValueError, match="only use train"):
        select_memorization_rows(train, [], manifest)


def test_duplicate_and_undersized_cohorts_are_rejected():
    with pytest.raises(ValueError, match="distinct"):
        select_memorization_rows([], [], {"record_ids": ["same"] * 12})
    with pytest.raises(ValueError, match="distinct"):
        select_memorization_rows([], [], {"record_ids": []})
