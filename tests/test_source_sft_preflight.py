import hashlib
import json

import pytest

from scripts.run_source_sft_mlx import stable_validation_sample
from triage_poc.source_sft_preflight import (
    SourceSftPreflightError,
    token_length_summary,
    validate_source_sft_artifacts,
)


def _write_jsonl(path, rows):
    content = "".join(json.dumps(row) + "\n" for row in rows)
    path.write_text(content)
    return {
        "path": path.name,
        "record_count": len(rows),
        "sha256": hashlib.sha256(content.encode()).hexdigest(),
    }


def _conversation(record_id):
    return {
        "record_id": record_id,
        "messages": [
            {"role": "system", "content": "system"},
            {"role": "user", "content": "question"},
            {"role": "assistant", "content": "answer"},
        ],
    }


def _fixture(tmp_path):
    canonical = [
        {"record_id": "train-id", "split": "train"},
        {"record_id": "validation-id", "split": "validation"},
        {"record_id": "test-id", "split": "test"},
    ]
    artifacts = {
        "canonical": _write_jsonl(tmp_path / "canonical.jsonl", canonical),
        "train_qwen3": _write_jsonl(tmp_path / "train.jsonl", [_conversation("train-id")]),
        "validation_qwen3": _write_jsonl(
            tmp_path / "validation.jsonl", [_conversation("validation-id")]
        ),
    }
    manifest = {
        "manifest_id": "derived-source-medical-qa-sft-v1",
        "status": "ready_for_local_educational_sft",
        "triage_label_count": 0,
        "artifacts": artifacts,
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest))
    return manifest_path


def test_validates_artifacts_and_test_isolation(tmp_path):
    manifest_path = _fixture(tmp_path)
    _, canonical, train, validation = validate_source_sft_artifacts(manifest_path, tmp_path)
    assert len(canonical) == 3
    assert len(train) == 1
    assert len(validation) == 1


def test_rejects_checksum_mismatch(tmp_path):
    manifest_path = _fixture(tmp_path)
    (tmp_path / "train.jsonl").write_text("{}\n")
    with pytest.raises(SourceSftPreflightError, match="Checksum mismatch"):
        validate_source_sft_artifacts(manifest_path, tmp_path)


def test_rejects_test_leakage(tmp_path):
    manifest_path = _fixture(tmp_path)
    manifest = json.loads(manifest_path.read_text())
    manifest["artifacts"]["train_qwen3"] = _write_jsonl(
        tmp_path / "train.jsonl", [_conversation("test-id")]
    )
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(SourceSftPreflightError, match="test split leaked"):
        validate_source_sft_artifacts(manifest_path, tmp_path)


def test_reports_token_length_distribution():
    class Tokenizer:
        def encode(self, text, add_special_tokens):
            assert add_special_tokens is True
            return text.split()

    summary = token_length_summary(
        [_conversation("one"), _conversation("two")],
        Tokenizer(),
        max_sequence_length=2,
    )
    assert summary["count"] == 2
    assert summary["maximum"] == 3
    assert summary["over_max_sequence_length"] == 2


def test_validation_sample_is_deterministic_and_unique():
    rows = [_conversation(f"record-{index}") for index in range(10)]
    first = stable_validation_sample(rows, 4, 42)
    second = stable_validation_sample(list(reversed(rows)), 4, 42)
    assert first == second
    assert len({row["record_id"] for row in first}) == 4
