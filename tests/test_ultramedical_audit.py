import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from triage_poc.ultramedical_audit import (
    audit_presidio_preference_sample,
    audit_ultramedical_preference,
)


@dataclass
class _Audit:
    detected_entity_counts: dict[str, int]
    residual_entity_counts: dict[str, int]
    status: str


@dataclass
class _Result:
    audit: _Audit


class _FakeAnonymizer:
    def anonymize(self, text: str, language: str) -> _Result:
        assert text
        assert language == "en"
        return _Result(_Audit({"PERSON": 1}, {}, "passed"))


def _row(prompt_id: str, prompt: str, label_type: str = "hard") -> dict[str, object]:
    return {
        "prompt_id": prompt_id,
        "label_type": label_type,
        "prompt": prompt,
        "chosen": [
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": "Better answer"},
        ],
        "rejected": [
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": "Worse answer"},
        ],
        "metadata": {
            "golden_answer": "A",
            "chosen": {"model": "model-a"},
            "rejected": {"model": "model-b"},
        },
    }


def _write_split(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows), encoding="utf-8")


def test_audit_preserves_test_for_evaluation_and_counts_overlap(tmp_path):
    _write_split(tmp_path / "dev.json", [_row("MedQA,1", "Same prompt")])
    _write_split(tmp_path / "test.json", [_row("MedQA,2", "SAME—PROMPT", "human")])

    report = audit_ultramedical_preference(tmp_path)

    assert report["train_downloaded"] is False
    assert report["allowed_split_use"]["test"] == "evaluation_only"
    assert report["cross_split_normalized_prompt_overlap"] == {"dev_test": 1}
    assert report["splits"]["dev"]["rows"] == 1
    assert report["splits"]["test"]["label_type_counts"] == {"human": 1}
    assert "Same prompt" not in str(report)


def test_audit_counts_duplicates_and_invalid_preference_pair(tmp_path):
    first = _row("MedQA,1", "Question one")
    second = _row("MedQA,1", "Question one")
    second["rejected"] = second["chosen"]
    _write_split(tmp_path / "dev.json", [first, second])
    _write_split(tmp_path / "test.json", [_row("MedQA,2", "Question two", "human")])

    report = audit_ultramedical_preference(tmp_path)

    dev = report["splits"]["dev"]
    assert dev["duplicate_prompt_id_instances"] == 1
    assert dev["duplicate_normalized_prompt_instances"] == 1
    assert dev["identical_chosen_rejected"] == 1


def test_audit_requires_both_small_splits(tmp_path):
    _write_split(tmp_path / "dev.json", [])

    with pytest.raises(ValueError, match="test.json"):
        audit_ultramedical_preference(tmp_path)


def test_audit_streams_optional_train_and_keeps_it_candidate_only(tmp_path):
    _write_split(tmp_path / "train.json", [_row("MedQA,0", "Training question")])
    _write_split(tmp_path / "dev.json", [_row("MedQA,1", "Dev question")])
    _write_split(tmp_path / "test.json", [_row("MedQA,2", "Test question", "human")])

    report = audit_ultramedical_preference(tmp_path)

    assert report["train_downloaded"] is True
    assert report["splits"]["train"]["rows"] == 1
    assert report["allowed_split_use"]["train"] == "candidate_training_only"


def test_presidio_sample_is_deterministic_and_text_free(tmp_path):
    _write_split(tmp_path / "dev.json", [_row("MedQA,1", "Question one")])
    _write_split(tmp_path / "test.json", [_row("MedQA,2", "Question two", "human")])

    first = audit_presidio_preference_sample(tmp_path, _FakeAnonymizer(), sample_per_split=1)
    second = audit_presidio_preference_sample(tmp_path, _FakeAnonymizer(), sample_per_split=1)

    assert first == second
    assert first["sample_count"] == 2
    assert first["detected_entity_counts"] == {"PERSON": 2}
    assert "Question" not in str(first)
