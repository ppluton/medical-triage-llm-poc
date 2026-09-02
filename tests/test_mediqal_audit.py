import json

from triage_poc.mediqal_audit import audit_mediqal


def _write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
    )


def test_audit_counts_rows_excludes_test_and_detects_overlap(tmp_path):
    base_row = {"id": "1", "question": "Same question", "correct_answers": "A"}
    _write_jsonl(tmp_path / "mcqu" / "train.json", [base_row])
    _write_jsonl(tmp_path / "mcqu" / "validation.json", [dict(base_row, id="2")])
    _write_jsonl(tmp_path / "mcqu" / "test.json", [dict(base_row, id="3")])
    _write_jsonl(
        tmp_path / "oeq" / "test.json",
        [{"id": "4", "question": "Open question", "answer": "Answer"}],
    )

    report = audit_mediqal(tmp_path)

    assert report["total_rows"] == 4
    assert report["authoring_eligible_rows"] == 2
    assert report["test_rows_excluded_from_authoring"] == 2
    assert report["normalized_question_split_overlaps"] == {
        "train_validation": 1,
        "train_test": 1,
        "validation_test": 1,
    }
    assert report["direct_triage_sft_eligible"] is False
