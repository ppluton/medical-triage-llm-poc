import json
from pathlib import Path

import pytest

from triage_poc.api import TriageRequest
from triage_poc.modal_deployment import (
    EXPECTED_ADAPTER_BASE,
    EXPECTED_ADAPTER_FILES,
    SELECTED_MODEL_NAME,
    build_vllm_command,
    sha256,
    validate_deployment_environment,
    verify_selected_adapter,
)


def _adapter(directory: Path) -> None:
    directory.mkdir()
    for name in EXPECTED_ADAPTER_FILES:
        value = (
            json.dumps({"base_model_name_or_path": EXPECTED_ADAPTER_BASE})
            if name == "adapter_config.json"
            else name
        )
        (directory / name).write_text(value)


def test_selected_adapter_verification_is_fail_closed(tmp_path, monkeypatch):
    adapter = tmp_path / "adapter"
    _adapter(adapter)
    expected = {name: sha256(adapter / name) for name in EXPECTED_ADAPTER_FILES}
    monkeypatch.setattr("triage_poc.modal_deployment.EXPECTED_ADAPTER_FILES", expected)

    result = verify_selected_adapter(adapter)
    assert result["model_name"] == SELECTED_MODEL_NAME
    assert result["files_verified"] == len(EXPECTED_ADAPTER_FILES)

    (adapter / "chat_template.jinja").write_text("changed")
    with pytest.raises(ValueError, match="checksum mismatch"):
        verify_selected_adapter(adapter)


def test_vllm_command_serves_only_the_selected_sft_adapter(tmp_path):
    base = tmp_path / "base"
    adapter = tmp_path / "adapter"
    command = build_vllm_command(base, adapter, port=8123)

    assert command[:3] == ["python", "-m", "vllm.entrypoints.openai.api_server"]
    assert command[command.index("--model") + 1] == str(base)
    assert command[command.index("--tokenizer") + 1] == str(adapter)
    assert command[command.index("--lora-modules") + 1] == f"{SELECTED_MODEL_NAME}={adapter}"
    assert command[command.index("--host") + 1] == "127.0.0.1"
    assert command[command.index("--port") + 1] == "8123"
    assert "chsa-dpo" not in command

    with pytest.raises(ValueError, match="port"):
        build_vllm_command(base, adapter, port=0)


def test_modal_smoke_sample_is_synthetic_and_bilingual():
    path = Path("data/samples/modal-smoke-scenarios.json")
    scenarios = json.loads(path.read_text())
    assert len(scenarios) == 2
    assert {row["request"]["language"] for row in scenarios} == {"fr", "en"}
    assert all(row.get("synthetic") is True for row in scenarios)
    assert all(TriageRequest.model_validate(row["request"]) for row in scenarios)


def test_deployment_environment_validation_returns_no_secrets():
    environment = {
        "MODAL_TOKEN_ID": "synthetic-modal-id",
        "MODAL_TOKEN_SECRET": "synthetic-modal-secret",
        "MODAL_ENVIRONMENT": "main",
        "TRIAGE_API_TOKEN": "x" * 32,
        "TRIAGE_MODAL_URL": "https://example--chsa-triage.modal.run",
    }
    result = validate_deployment_environment(environment)
    assert result == {
        "status": "deployment_environment_valid",
        "modal_environment": "main",
        "endpoint_host": "example--chsa-triage.modal.run",
    }
    serialized = json.dumps(result)
    assert environment["MODAL_TOKEN_SECRET"] not in serialized
    assert environment["TRIAGE_API_TOKEN"] not in serialized

    with pytest.raises(ValueError, match="credential-free HTTPS origin"):
        validate_deployment_environment({**environment, "TRIAGE_MODAL_URL": "http://bad"})
    with pytest.raises(ValueError, match="at least 32"):
        validate_deployment_environment({**environment, "TRIAGE_API_TOKEN": "short"})

    predeploy = dict(environment)
    del predeploy["TRIAGE_MODAL_URL"]
    assert validate_deployment_environment(predeploy, require_endpoint=False) == {
        "status": "predeployment_environment_valid",
        "modal_environment": "main",
    }
