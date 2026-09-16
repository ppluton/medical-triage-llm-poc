#!/usr/bin/env python3
"""Serve the selected SFT on free Kaggle GPU through a temporary Cloudflare URL."""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import signal
import subprocess
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from triage_poc.free_demo import (
    cloudflared_command,
    extract_quick_tunnel_url,
    validate_demo_token,
)
from triage_poc.modal_deployment import (
    SELECTED_MODEL_NAME,
    SELECTED_MODEL_VERSION,
    build_vllm_command,
    verify_modal_assets,
)

PINNED_CLOUDFLARED_SHA256 = "03f1f25d1cc93b9ad6c60569d44060bc4f17ed97075760ed8cfca4b12dcd68cc"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def wait_ready(url: str, process: subprocess.Popen, timeout: int, token: str | None = None):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("Owned service exited before readiness; inspect its log")
        request = urllib.request.Request(url)
        if token:
            request.add_header("Authorization", "Bearer " + token)
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                if response.status == 200:
                    return json.load(response)
        except (urllib.error.URLError, TimeoutError):
            pass
        time.sleep(2)
    raise TimeoutError("Owned service readiness deadline exceeded")


def stop_owned(process: subprocess.Popen | None) -> None:
    if process is None or process.poll() is not None:
        return
    os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=10)


def configure_cuda_linker(environment: dict[str, str], output: Path) -> None:
    """Expose Kaggle's mounted CUDA driver to vLLM JIT linking."""
    ctypes.CDLL("libcuda.so.1")
    candidates = []
    for line in Path("/proc/self/maps").read_text().splitlines():
        fields = line.split(maxsplit=5)
        if len(fields) == 6 and Path(fields[5]).name.startswith("libcuda.so"):
            candidates.append(Path(fields[5]))
    driver = next((path.resolve() for path in candidates if path.is_file()), None)
    if driver is None:
        raise RuntimeError("Loaded CUDA driver path not found")
    directory = output / "cuda-linker"
    directory.mkdir()
    (directory / "libcuda.so").symlink_to(driver)
    environment["LIBRARY_PATH"] = os.pathsep.join(
        filter(None, (str(directory.resolve()), environment.get("LIBRARY_PATH")))
    )


def wait_for_tunnel(log_path: Path, process: subprocess.Popen, timeout: int) -> str:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("Cloudflare Quick Tunnel exited before publishing a URL")
        url = extract_quick_tunnel_url(log_path.read_text(errors="replace"))
        if url:
            return url
        time.sleep(1)
    raise TimeoutError("Cloudflare Quick Tunnel URL deadline exceeded")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vllm-python", type=Path, required=True)
    parser.add_argument("--api-python", type=Path, required=True)
    parser.add_argument("--cloudflared", type=Path, required=True)
    parser.add_argument("--base-model", type=Path, required=True)
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()

    validate_demo_token(dict(os.environ))
    if not args.cloudflared.is_file():
        raise ValueError("Pinned cloudflared binary is missing")
    if sha256(args.cloudflared) != PINNED_CLOUDFLARED_SHA256:
        raise ValueError("cloudflared checksum mismatch")
    identity = verify_modal_assets(args.base_model, args.adapter)
    if args.preflight:
        print(json.dumps({"status": "preflight_passed", "identity": identity}, indent=2))
        return
    if args.output.exists():
        raise ValueError("Fresh demonstration output required")
    args.output.mkdir(parents=True)

    root = Path(__file__).resolve().parents[1]
    token = os.environ["TRIAGE_API_TOKEN"]
    environment = dict(
        os.environ,
        CUDA_VISIBLE_DEVICES="0",
        PYTHONPATH=str(root / "src"),
        PYTHONUNBUFFERED="1",
        VLLM_NO_USAGE_STATS="1",
    )
    configure_cuda_linker(environment, args.output)
    processes: list[subprocess.Popen] = []
    try:
        vllm_command = build_vllm_command(args.base_model, args.adapter)
        vllm_command[0] = str(args.vllm_python)
        with (args.output / "vllm.log").open("w") as log:
            vllm = subprocess.Popen(
                vllm_command,
                stdout=log,
                stderr=subprocess.STDOUT,
                env=environment,
                start_new_session=True,
            )
        processes.append(vllm)
        models = wait_ready("http://127.0.0.1:8001/v1/models", vllm, 900)
        if SELECTED_MODEL_NAME not in {row.get("id") for row in models.get("data", [])}:
            raise RuntimeError("Selected SFT adapter is absent from the model registry")

        api_environment = dict(
            environment,
            TRIAGE_VLLM_URL="http://127.0.0.1:8001/v1",
            TRIAGE_MODEL_NAME=SELECTED_MODEL_NAME,
            TRIAGE_MODEL_VERSION=SELECTED_MODEL_VERSION,
            TRIAGE_AUDIT_PATH=str(args.output / "audit.jsonl"),
        )
        with (args.output / "api.log").open("w") as log:
            api = subprocess.Popen(
                [
                    str(args.api_python),
                    "-m",
                    "uvicorn",
                    "triage_poc.serving:create_serving_app",
                    "--factory",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "8000",
                    "--no-access-log",
                ],
                stdout=log,
                stderr=subprocess.STDOUT,
                env=api_environment,
                start_new_session=True,
            )
        processes.append(api)
        wait_ready("http://127.0.0.1:8000/healthz", api, 120, token)

        tunnel_log = args.output / "cloudflared.log"
        with tunnel_log.open("w") as log:
            tunnel = subprocess.Popen(
                cloudflared_command(args.cloudflared),
                stdout=log,
                stderr=subprocess.STDOUT,
                env=environment,
                start_new_session=True,
            )
        processes.append(tunnel)
        public_url = wait_for_tunnel(tunnel_log, tunnel, 120)
        wait_ready(public_url + "/healthz", tunnel, 120, token)
        metadata = {
            "status": "temporary_demo_ready",
            "created_at": datetime.now(UTC).isoformat(),
            "public_url": public_url,
            "model_name": SELECTED_MODEL_NAME,
            "model_version": SELECTED_MODEL_VERSION,
            "base_revision": identity["base"]["revision"],
            "authentication": "bearer_required",
            "public_endpoint": True,
            "ephemeral": True,
            "cost_commitment_usd": 0,
            "clinical_validation": False,
            "limits": [
                "Development-only Quick Tunnel without an uptime SLA.",
                "Endpoint disappears when the Kaggle session or this process stops.",
                "No patient-identifiable or real clinical data is authorized.",
            ],
        }
        (args.output / "endpoint.json").write_text(json.dumps(metadata, indent=2) + "\n")
        print(json.dumps(metadata, indent=2), flush=True)
        while all(process.poll() is None for process in processes):
            time.sleep(2)
        raise RuntimeError("A demonstration service stopped unexpectedly")
    except KeyboardInterrupt:
        pass
    finally:
        for process in reversed(processes):
            stop_owned(process)


if __name__ == "__main__":
    main()
