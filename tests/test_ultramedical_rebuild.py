import json
from pathlib import Path

from triage_poc.ultramedical_rebuild import rebuild_ultramedical_splits


def _row(prompt_id: str, prompt: str, chosen: str = "Good", rejected: str = "Bad"):
    return {
        "prompt_id": prompt_id,
        "label_type": "hard",
        "prompt": prompt,
        "chosen": [
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": chosen},
        ],
        "rejected": [
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": rejected},
        ],
        "metadata": {},
    }


def _write(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows), encoding="utf-8")


def test_rebuild_applies_test_then_dev_precedence_without_source_text(tmp_path):
    data = tmp_path / "data"
    _write(
        data / "train.json",
        [
            _row("1", "Test overlap"),
            _row("2", "Dev overlap"),
            _row("3", "Training only"),
        ],
    )
    _write(data / "dev.json", [_row("4", "TEST—OVERLAP"), _row("5", "Dev overlap")])
    _write(data / "test.json", [_row("6", "test overlap")])
    output = tmp_path / "index.jsonl"

    report = rebuild_ultramedical_splits(data, output)
    records = [json.loads(line) for line in output.read_text().splitlines()]

    assert report["decision_counts"] == {
        "candidate_training": 1,
        "candidate_validation": 1,
        "excluded_dev_overlap": 1,
        "excluded_test_overlap": 2,
        "reserved_evaluation": 1,
    }
    assert report["unique_kept_prompt_groups"] == {
        "candidate_training": 1,
        "candidate_validation": 1,
        "reserved_evaluation": 1,
    }
    assert "Training only" not in output.read_text()
    assert all(record["prompt_group_sha256"] for record in records)
    assert report["output"]["contains_source_text"] is False


def test_rebuild_excludes_exact_duplicate_preferences_but_keeps_distinct_pairs(tmp_path):
    data = tmp_path / "data"
    repeated = _row("1", "One prompt")
    distinct = _row("1", "One prompt", chosen="Alternative good")
    _write(data / "train.json", [repeated, repeated, distinct])
    _write(data / "dev.json", [])
    _write(data / "test.json", [])

    report = rebuild_ultramedical_splits(data, tmp_path / "index.jsonl")

    assert report["decision_counts"] == {
        "candidate_training": 2,
        "excluded_exact_duplicate": 1,
    }
    assert report["unique_kept_prompt_groups"]["candidate_training"] == 1
    assert report["duplicate_preference_instances"]["train"] == 1


def test_rebuild_is_deterministic(tmp_path):
    data = tmp_path / "data"
    _write(data / "train.json", [_row("1", "Train")])
    _write(data / "dev.json", [_row("2", "Dev")])
    _write(data / "test.json", [_row("3", "Test")])

    first = rebuild_ultramedical_splits(data, tmp_path / "first.jsonl")
    second = rebuild_ultramedical_splits(data, tmp_path / "second.jsonl")

    assert first["output"]["sha256"] == second["output"]["sha256"]
    assert (tmp_path / "first.jsonl").read_bytes() == (tmp_path / "second.jsonl").read_bytes()
