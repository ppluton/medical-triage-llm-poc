"""Fail-closed identity checks and vLLM command for the Modal demonstration."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from urllib.parse import urlparse

from triage_poc.model_snapshot import BASE_SERVED_MODEL_NAME, verify_base_snapshot

SELECTED_MODEL_NAME = "chsa-selected"
SELECTED_MODEL_VERSION = "c911f9c631be825f4af5c7dff5a87409d1ee91d4c28e2b0b1571e808e055d413"
MODAL_APP_NAME = "chsa-triage-demo"
MODAL_SERVER_NAME = "TriageService"
EXPECTED_ADAPTER_BASE = "/kaggle/input/qwen3-1-7b-base-e249956c"
EXPECTED_ADAPTER_FILES = {
    "adapter_model.safetensors": SELECTED_MODEL_VERSION,
    "adapter_config.json": "5b533994412bd4a635c52d1c43026f30046515a5b25aa07ea86b9c91f3eaf6cb",
    "tokenizer.json": "be75606093db2094d7cd20f3c2f385c212750648bd6ea4fb2bf507a6a4c55506",
    "tokenizer_config.json": "99edf6e0f078f19ec1be394705811708c274663768997ca32b9e4c0cbf4447f5",
    "chat_template.jinja": "b44d8063c3b49558db444116213856583a953510918d3eac9c58bf1b35c905b0",
}


def validate_deployment_environment(
    environment: dict[str, str] | None = None,
    *,
    require_endpoint: bool = True,
) -> dict:
    """Validate deployment inputs without returning or printing any credential."""
    environment = dict(os.environ if environment is None else environment)
    required = [
        "MODAL_TOKEN_ID",
        "MODAL_TOKEN_SECRET",
        "MODAL_ENVIRONMENT",
        "TRIAGE_API_TOKEN",
    ]
    if require_endpoint:
        required.append("TRIAGE_MODAL_URL")
    missing = [name for name in required if not environment.get(name)]
    if missing:
        raise ValueError(f"Missing deployment environment values: {missing}")
    if len(environment["TRIAGE_API_TOKEN"]) < 32:
        raise ValueError("TRIAGE_API_TOKEN must contain at least 32 characters")
    if not require_endpoint:
        return {
            "status": "predeployment_environment_valid",
            "modal_environment": environment["MODAL_ENVIRONMENT"],
        }
    parsed = urlparse(environment["TRIAGE_MODAL_URL"])
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
    ):
        raise ValueError("TRIAGE_MODAL_URL must be a credential-free HTTPS origin")
    return {
        "status": "deployment_environment_valid",
        "modal_environment": environment["MODAL_ENVIRONMENT"],
        "endpoint_host": parsed.hostname,
    }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_selected_adapter(adapter_directory: Path) -> dict:
    """Reject a missing, changed, or differently based selected SFT adapter."""
    adapter_directory = Path(adapter_directory)
    for name, expected in EXPECTED_ADAPTER_FILES.items():
        path = adapter_directory / name
        if not path.is_file() or sha256(path) != expected:
            raise ValueError(f"Selected SFT adapter checksum mismatch: {name}")
    config = json.loads((adapter_directory / "adapter_config.json").read_text())
    if config.get("base_model_name_or_path") != EXPECTED_ADAPTER_BASE:
        raise ValueError("Selected SFT adapter does not identify the frozen Base snapshot")
    return {
        "model_name": SELECTED_MODEL_NAME,
        "model_version": SELECTED_MODEL_VERSION,
        "files_verified": len(EXPECTED_ADAPTER_FILES),
        "clinical_validation": "not_performed",
    }


def verify_modal_assets(base_directory: Path, adapter_directory: Path) -> dict:
    """Verify both immutable model layers before the GPU process starts."""
    return {
        "base": verify_base_snapshot(base_directory),
        "adapter": verify_selected_adapter(adapter_directory),
    }


def build_vllm_command(
    base_directory: Path,
    adapter_directory: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 8001,
) -> list[str]:
    """Return the exact single-adapter command previously exercised by the POC."""
    if not 1 <= port <= 65535:
        raise ValueError("vLLM port must be between 1 and 65535")
    base_directory = Path(base_directory)
    adapter_directory = Path(adapter_directory)
    return [
        "python",
        "-m",
        "vllm.entrypoints.openai.api_server",
        "--model",
        str(base_directory),
        "--served-model-name",
        BASE_SERVED_MODEL_NAME,
        "--tokenizer",
        str(adapter_directory),
        "--chat-template",
        str(adapter_directory / "chat_template.jinja"),
        "--dtype",
        "half",
        "--max-model-len",
        "4096",
        "--max-num-seqs",
        "1",
        "--enforce-eager",
        "--enable-lora",
        "--max-lora-rank",
        "16",
        "--lora-modules",
        f"{SELECTED_MODEL_NAME}={adapter_directory}",
        "--host",
        host,
        "--port",
        str(port),
    ]
