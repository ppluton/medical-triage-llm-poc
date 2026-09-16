"""Cost-bounded Modal target for the private CHSA educational demonstration.

This module only declares resources. ``modal deploy -m deploy.modal_app`` is the
external, potentially billable action and must not be run without explicit approval.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

import modal

from triage_poc.modal_deployment import (
    MODAL_APP_NAME,
    SELECTED_MODEL_NAME,
    SELECTED_MODEL_VERSION,
    build_vllm_command,
    verify_modal_assets,
)

APP_NAME = MODAL_APP_NAME
MODEL_VOLUME_NAME = "chsa-triage-models-v1"
AUDIT_VOLUME_NAME = "chsa-triage-audit-v1"
API_SECRET_NAME = "chsa-triage-api-v1"
BASE_DIRECTORY = Path("/models/base")
ADAPTER_DIRECTORY = Path("/models/adapter")
AUDIT_PATH = Path("/audit/interactions.jsonl")
VLLM_PORT = 8001

VLLM_IMAGE = (
    "vllm/vllm-openai:v0.15.0@sha256:"
    "97187c9535fd6d6040444d68bb073f17344fd454e9241cc7a4e998141f244543"
)
SPACY_MODELS = (
    "https://github.com/explosion/spacy-models/releases/download/"
    "fr_core_news_md-3.8.0/fr_core_news_md-3.8.0-py3-none-any.whl",
    "https://github.com/explosion/spacy-models/releases/download/"
    "en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl",
)

image = (
    modal.Image.from_registry(
        VLLM_IMAGE,
        setup_dockerfile_commands=[
            "RUN ln -sf /usr/bin/python3 /usr/bin/python",
        ],
    )
    .entrypoint([])
    .add_local_file("requirements/api.txt", "/tmp/chsa/requirements-api.txt", copy=True)
    .add_local_file("pyproject.toml", "/tmp/chsa/project/pyproject.toml", copy=True)
    .add_local_file("README.md", "/tmp/chsa/project/README.md", copy=True)
    .add_local_dir("src", "/tmp/chsa/project/src", copy=True)
    .run_commands(
        "python3 -m venv /opt/chsa-api",
        "/opt/chsa-api/bin/pip install --no-cache-dir -r /tmp/chsa/requirements-api.txt",
        "/opt/chsa-api/bin/pip install --no-cache-dir --no-deps /tmp/chsa/project",
        "/opt/chsa-api/bin/pip install --no-cache-dir --no-deps " + " ".join(SPACY_MODELS),
    )
    .add_local_dir("src/triage_poc", "/root/triage_poc", copy=True)
    .env({"PYTHONPATH": "/root", "VLLM_NO_USAGE_STATS": "1", "PYTHONUNBUFFERED": "1"})
)

model_volume = modal.Volume.from_name(MODEL_VOLUME_NAME)
audit_volume = modal.Volume.from_name(AUDIT_VOLUME_NAME)
api_secret = modal.Secret.from_name(API_SECRET_NAME)
app = modal.App(APP_NAME)


def _wait_for_http(
    url: str,
    process: subprocess.Popen,
    *,
    timeout_seconds: int,
    token: str | None = None,
) -> dict:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(
                "Owned service exited before readiness; inspect Modal container logs"
            )
        try:
            request = urllib.request.Request(url)
            if token:
                request.add_header("Authorization", "Bearer " + token)
            with urllib.request.urlopen(request, timeout=3) as response:
                if response.status == 200:
                    return json.load(response)
        except (urllib.error.URLError, TimeoutError):
            pass
        time.sleep(2)
    raise TimeoutError("Owned service readiness deadline exceeded")


@app.server(
    image=image,
    gpu="T4",
    secrets=[api_secret],
    volumes={
        "/models": model_volume.with_mount_options(read_only=True),
        "/audit": audit_volume,
    },
    min_containers=0,
    max_containers=1,
    scaledown_window=120,
    startup_timeout=1200,
    port=8000,
    target_concurrency=1,
    unauthenticated=True,
)
class TriageService:
    @modal.enter()
    def start_services(self) -> None:
        evidence = verify_modal_assets(BASE_DIRECTORY, ADAPTER_DIRECTORY)
        print(
            json.dumps(
                {
                    "event": "verified_model_assets",
                    "base_revision": evidence["base"]["revision"],
                    "adapter_sha256": evidence["adapter"]["model_version"],
                }
            )
        )
        env = dict(os.environ, CUDA_VISIBLE_DEVICES="0")
        self.vllm_process = subprocess.Popen(
            build_vllm_command(BASE_DIRECTORY, ADAPTER_DIRECTORY, port=VLLM_PORT),
            env=env,
            start_new_session=True,
        )
        models = _wait_for_http(
            f"http://127.0.0.1:{VLLM_PORT}/v1/models",
            self.vllm_process,
            timeout_seconds=900,
        )
        served = {row.get("id") for row in models.get("data", [])}
        if SELECTED_MODEL_NAME not in served:
            raise RuntimeError("Selected SFT adapter is absent from the vLLM model registry")

        token = os.environ.get("TRIAGE_API_TOKEN", "")
        if len(token) < 32:
            raise ValueError("TRIAGE_API_TOKEN must contain at least 32 characters")
        api_env = dict(
            os.environ,
            TRIAGE_VLLM_URL=f"http://127.0.0.1:{VLLM_PORT}/v1",
            TRIAGE_MODEL_NAME=SELECTED_MODEL_NAME,
            TRIAGE_MODEL_VERSION=SELECTED_MODEL_VERSION,
            TRIAGE_AUDIT_PATH=str(AUDIT_PATH),
            TRIAGE_AUDIT_SYNC_PARENT="1",
        )
        self.api_process = subprocess.Popen(
            [
                "/opt/chsa-api/bin/python",
                "-m",
                "uvicorn",
                "triage_poc.serving:create_serving_app",
                "--factory",
                "--host",
                "0.0.0.0",
                "--port",
                "8000",
                "--no-access-log",
            ],
            env=api_env,
            start_new_session=True,
        )
        _wait_for_http(
            "http://127.0.0.1:8000/healthz",
            self.api_process,
            timeout_seconds=120,
            token=token,
        )

    @modal.exit()
    def stop_services(self) -> None:
        for attribute in ("api_process", "vllm_process"):
            process = getattr(self, attribute, None)
            if process is not None and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=10)
