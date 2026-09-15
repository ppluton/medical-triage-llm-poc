import json

import pytest

from scripts.build_kaggle_vllm_demo import BASE_DATASET_ID, attach_base_dataset
from scripts.run_vllm_api_demo import summarize_guardrail_audit
from triage_poc.model_snapshot import (
    EXPECTED_BASE_REVISION,
    sha256,
    verify_base_snapshot,
)


def _response(identifier, success=True):
    return {
        "id": identifier,
        "success": success,
        "response": {"interaction_id": f"interaction-{identifier}"},
    }


def test_guardrail_audit_summary_is_text_free_and_versioned(tmp_path):
    report = tmp_path / "endpoint.json"
    audit = tmp_path / "audit.jsonl"
    report.write_text(json.dumps({"records": [_response("one"), _response("two")]}))
    audit.write_text(
        "\n".join(
            json.dumps(row)
            for row in (
                {
                    "interaction_id": "interaction-one",
                    "guardrail_status": "model_output",
                    "guardrail_version": "proposed-guardrails-v1",
                    "guardrail_reasons": [],
                    "anonymized_input": {"symptoms": ["private synthetic text"]},
                },
                {
                    "interaction_id": "interaction-two",
                    "guardrail_status": "safe_fallback",
                    "guardrail_version": "proposed-guardrails-v1",
                    "guardrail_reasons": ["invented_stability_or_absence"],
                    "anonymized_input": {"symptoms": ["other private synthetic text"]},
                },
            )
        )
        + "\n"
    )

    summary = summarize_guardrail_audit(report, audit)

    assert summary["status"] == "passed"
    assert summary["guardrail_status_counts"] == {"model_output": 1, "safe_fallback": 1}
    assert summary["guardrail_reason_counts"] == {"invented_stability_or_absence": 1}
    assert "private synthetic text" not in json.dumps(summary)


def test_guardrail_audit_summary_rejects_missing_or_unversioned_entries(tmp_path):
    report = tmp_path / "endpoint.json"
    audit = tmp_path / "audit.jsonl"
    report.write_text(json.dumps({"records": [_response("one"), _response("missing")]}))
    audit.write_text(
        json.dumps(
            {
                "interaction_id": "interaction-one",
                "guardrail_status": "corrected",
                "guardrail_version": "old-version",
                "guardrail_reasons": ["priority_floor"],
            }
        )
        + "\n"
    )

    summary = summarize_guardrail_audit(report, audit)

    assert summary["status"] == "failed"
    assert summary["issue_counts"] == {
        "missing_or_duplicate_audit_entry": 1,
        "unexpected_guardrail_version": 1,
    }


def _base_snapshot(tmp_path):
    directory = tmp_path / "base"
    directory.mkdir()
    (directory / "model.safetensors").write_bytes(b"synthetic model")
    (directory / "tokenizer.json").write_text("synthetic tokenizer")
    model_sha = sha256(directory / "model.safetensors")
    manifest = {
        "source": {"revision": EXPECTED_BASE_REVISION},
        "license": {"spdx": "Apache-2.0"},
        "model_sha256": model_sha,
        "files": {
            name: {"size": (directory / name).stat().st_size, "sha256": sha256(directory / name)}
            for name in ("model.safetensors", "tokenizer.json")
        },
    }
    manifest_path = directory / "MODEL_SNAPSHOT_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest) + "\n")
    return directory, sha256(manifest_path), model_sha


def test_base_snapshot_verifies_manifest_model_and_tokenizer(tmp_path):
    directory, manifest_sha, model_sha = _base_snapshot(tmp_path)

    result = verify_base_snapshot(
        directory,
        expected_manifest_sha256=manifest_sha,
        expected_model_sha256=model_sha,
    )

    assert result["revision"] == EXPECTED_BASE_REVISION
    assert result["files_verified"] == 2


def test_base_snapshot_fails_closed_when_attached_file_changes(tmp_path):
    directory, manifest_sha, model_sha = _base_snapshot(tmp_path)
    (directory / "tokenizer.json").write_text("modified")

    with pytest.raises(ValueError, match="tokenizer.json"):
        verify_base_snapshot(
            directory,
            expected_manifest_sha256=manifest_sha,
            expected_model_sha256=model_sha,
        )


def test_builder_attaches_private_base_dataset_once():
    metadata = {"dataset_sources": ["pierrepluton/existing", BASE_DATASET_ID]}

    result = attach_base_dataset(metadata)

    assert result["dataset_sources"] == ["pierrepluton/existing", BASE_DATASET_ID]
