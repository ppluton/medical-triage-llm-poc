from triage_poc.sft_isolation import cross_split_groups, isolate_groups


def test_transitive_groups_preserve_test_and_never_move_rows():
    rows = [
        {"record_id": rid, "split": split}
        for rid, split in [("a", "train"), ("b", "validation"), ("c", "test"), ("d", "train")]
    ]
    keys = {"a": ["doc1"], "b": ["doc1", "answer2"], "c": ["answer2"], "d": ["doc4"]}
    kept, removed = isolate_groups(rows, keys)
    assert kept == rows[2:]
    assert {r["record_id"] for r in removed} == {"a", "b"}
    assert cross_split_groups(kept, keys) == 0
    assert rows[0]["split"] == "train"


def test_same_split_groups_are_retained():
    rows = [{"record_id": rid, "split": "train"} for rid in ("a", "b")]
    assert isolate_groups(rows, {"a": ["same"], "b": ["same"]}) == (rows, [])
