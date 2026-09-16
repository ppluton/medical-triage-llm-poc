import json

import pytest

from scripts.build_kaggle_model_snapshot import build_snapshot, sha256


def _snapshot(tmp_path, revision):
    snapshot = tmp_path / revision
    snapshot.mkdir()
    for name in (
        ".gitattributes",
        "added_tokens.json",
        "config.json",
        "generation_config.json",
        "merges.txt",
        "special_tokens_map.json",
        "tokenizer.json",
        "tokenizer_config.json",
        "vocab.json",
    ):
        (snapshot / name).write_text(name)
    (snapshot / "README.md").write_text(
        "---\nbase_model:\n- Qwen/Qwen3-1.7B-Base\nlicense: apache-2.0\n---\n"
    )
    (snapshot / "model.safetensors").write_bytes(b"synthetic-model")
    return snapshot


def test_build_snapshot_preserves_exact_revision_tokenizer_and_checksums(tmp_path):
    revision = "a" * 40
    snapshot = _snapshot(tmp_path, revision)
    output = tmp_path / "package"

    manifest = build_snapshot(
        snapshot,
        output,
        revision=revision,
        expected_model_sha256=sha256(snapshot / "model.safetensors"),
        dataset_id="pierrepluton/qwen3-1-7b-base-test",
    )

    assert manifest["source"]["revision"] == revision
    assert manifest["license"]["spdx"] == "Apache-2.0"
    assert manifest["files"]["tokenizer.json"]["sha256"] == sha256(
        snapshot / "tokenizer.json"
    )
    assert (output / "tokenizer.json").read_text() == "tokenizer.json"
    metadata = json.loads((output / "dataset-metadata.json").read_text())
    assert metadata["id"] == "pierrepluton/qwen3-1-7b-base-test"
    assert metadata["licenses"] == [{"name": "apache-2.0"}]


def test_build_snapshot_fails_before_output_on_model_checksum_mismatch(tmp_path):
    revision = "b" * 40
    snapshot = _snapshot(tmp_path, revision)
    output = tmp_path / "package"

    with pytest.raises(ValueError, match="checksum mismatch"):
        build_snapshot(
            snapshot,
            output,
            revision=revision,
            expected_model_sha256="0" * 64,
            dataset_id="pierrepluton/qwen3-1-7b-base-test",
        )

    assert not output.exists()


def test_build_snapshot_refuses_missing_license_declaration(tmp_path):
    revision = "c" * 40
    snapshot = _snapshot(tmp_path, revision)
    (snapshot / "README.md").write_text("license: unknown\n")

    with pytest.raises(ValueError, match="Apache-2.0"):
        build_snapshot(
            snapshot,
            tmp_path / "package",
            revision=revision,
            expected_model_sha256=sha256(snapshot / "model.safetensors"),
            dataset_id="pierrepluton/qwen3-1-7b-base-test",
        )
