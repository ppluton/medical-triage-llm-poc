import pytest

from triage_poc.sft_review_batch import (
    build_review_items,
    select_stratified_groups,
    summarize_review_items,
)


def _records():
    records = []
    index = 0
    for risk in ("chest_pain", "respiratory_distress"):
        for source in ("source-a", "source-b"):
            for _ in range(3):
                group_hash = f"{index:020x}"
                for language in ("fr", "en"):
                    records.append(
                        {
                            "candidate_id": f"sft-candidate-{group_hash}-{language}",
                            "bilingual_group_id": f"sft-authoring-group-{group_hash}",
                            "requested_language": language,
                            "requested_risk_family": risk,
                            "source": {"source_dataset": source},
                            "grounding": {
                                "question": "Synthetic question",
                                "answer": "Synthetic answer",
                                "truncated": False,
                            },
                            "draft": {"triage_level": None},
                            "split": None,
                            "training_eligible": False,
                        }
                    )
                index += 1
    return records


def test_selects_complete_deterministic_stratified_groups():
    first = select_stratified_groups(_records(), group_count=8, seed="test-seed")
    second = select_stratified_groups(_records(), group_count=8, seed="test-seed")

    assert [group["group_id"] for group in first] == [group["group_id"] for group in second]
    assert {(group["risk_family"], group["source_dataset"]) for group in first} == {
        ("chest_pain", "source-a"),
        ("chest_pain", "source-b"),
        ("respiratory_distress", "source-a"),
        ("respiratory_distress", "source-b"),
    }
    assert all(len(group["members"]) == 2 for group in first)


def test_review_items_remain_pending_and_non_clinical():
    groups = select_stratified_groups(_records(), group_count=4, seed="test-seed")
    items = build_review_items(groups)
    summary = summarize_review_items(items)

    assert summary["review_item_count"] == 4
    assert summary["candidate_count"] == 8
    assert summary["review_status_counts"] == {"pending": 4}
    assert all(item["clinical_validation_status"] == "not_started" for item in items)
    assert all(item["allowed_next_action"] == "manual_review_only" for item in items)


def test_rejects_any_training_eligible_input():
    records = _records()
    records[0]["training_eligible"] = True

    with pytest.raises(ValueError, match="non-trainable"):
        select_stratified_groups(records, group_count=1, seed="test-seed")
