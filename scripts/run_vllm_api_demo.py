#!/usr/bin/env python3
"""Run a loopback-only real-model API demonstration and preserve failed measurements."""

import argparse
import ctypes
import hashlib
import json
import os
import secrets
import signal
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path


def wait_ready(url, process, timeout, token=None):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("Owned server exited before readiness; inspect its saved log")
        request = urllib.request.Request(url)
        if token:
            request.add_header("Authorization", "Bearer " + token)
        try:
            with urllib.request.urlopen(request, timeout=3) as response:
                if response.status == 200:
                    return json.load(response)
        except (urllib.error.URLError, TimeoutError):
            pass
        time.sleep(2)
    raise TimeoutError("Owned server readiness deadline exceeded")


def stop_owned(process):
    if process and process.poll() is None:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=10)


def configure_cuda_linker(env, output):
    """Expose the installed driver to JIT linking without changing system libraries."""
    # Container-mounted driver libraries need not appear in the ldconfig cache.
    driver_handle = ctypes.CDLL("libcuda.so.1")
    candidates = []
    for line in Path("/proc/self/maps").read_text().splitlines():
        fields = line.split(maxsplit=5)
        if len(fields) == 6 and Path(fields[5]).name.startswith("libcuda.so"):
            candidates.append(Path(fields[5]))
    driver = next((path.resolve() for path in candidates if path.is_file()), None)
    if driver is None or driver_handle is None:
        raise RuntimeError("Loaded CUDA driver path not found in process mappings")
    directory = output / "cuda-linker"
    directory.mkdir()
    (directory / "libcuda.so").symlink_to(driver)
    env["LIBRARY_PATH"] = os.pathsep.join(
        filter(None, (str(directory.resolve()), env.get("LIBRARY_PATH")))
    )
    (output / "cuda-linker.json").write_text(
        json.dumps({"driver_library": str(driver), "link_directory": str(directory)}, indent=2)
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("vllm-python", "api-python", "sft", "dpo", "output", "scenarios"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.output.exists():
        raise ValueError("Fresh demonstration output required")
    expected = {
        "sft": "5c195a8c83bfd6493e7ffd74ec20e3d97207f9b650850aabd8de25afffea626d",
        "dpo": "6eda116c8bec89596c83beb09342094758db23abed5fa3391330965713ec85fd",
    }
    for name in expected:
        if (
            hashlib.sha256(
                (getattr(args, name) / "adapter_model.safetensors").read_bytes()
            ).hexdigest()
            != expected[name]
        ):
            raise ValueError("Unexpected adapter artifact")
    cases = json.loads(args.scenarios.read_text())
    if len(cases) != 18 or any(
        case.get("synthetic") is not True or case.get("split") != "development" for case in cases
    ):
        raise ValueError("Eighteen synthetic development scenarios required")
    args.output.mkdir(parents=True)
    env = dict(
        os.environ,
        CUDA_VISIBLE_DEVICES="0",
        PYTHONPATH=str(root / "src"),
        VLLM_NO_USAGE_STATS="1",
        PYTHONUNBUFFERED="1",
    )
    configure_cuda_linker(env, args.output)
    token = secrets.token_urlsafe(32)
    model_process = api_process = None
    reports = {}
    try:
        command = [
            str(args.vllm_python),
            "-m",
            "vllm.entrypoints.openai.api_server",
            "--model",
            "unsloth/Qwen3-1.7B-Base",
            "--revision",
            "e249956c10337100486d07afb77e3eb2b30906b8",
            "--tokenizer",
            str(args.sft),
            "--chat-template",
            str(args.sft / "chat_template.jinja"),
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
            f"chsa-sft={args.sft}",
            f"chsa-dpo={args.dpo}",
            "--host",
            "127.0.0.1",
            "--port",
            "8001",
        ]
        with (args.output / "vllm.log").open("w") as log:
            model_process = subprocess.Popen(
                command, stdout=log, stderr=subprocess.STDOUT, env=env, start_new_session=True
            )
        models = wait_ready("http://127.0.0.1:8001/v1/models", model_process, 900)
        (args.output / "models.json").write_text(json.dumps(models, indent=2))
        if not {"chsa-sft", "chsa-dpo"} <= {model["id"] for model in models["data"]}:
            raise ValueError("Expected LoRA models are not served")
        for stage in ("sft", "dpo"):
            directory = args.output / stage
            directory.mkdir()
            stage_env = dict(
                env,
                TRIAGE_API_TOKEN=token,
                TRIAGE_VLLM_URL="http://127.0.0.1:8001/v1",
                TRIAGE_MODEL_NAME=f"chsa-{stage}",
                TRIAGE_MODEL_VERSION=expected[stage],
                TRIAGE_AUDIT_PATH=str(directory / "audit.jsonl"),
            )
            with (directory / "api.log").open("w") as log:
                api_process = subprocess.Popen(
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
                    env=stage_env,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
            wait_ready("http://127.0.0.1:8000/healthz", api_process, 120, token)
            measure = subprocess.run(
                [
                    str(args.api_python),
                    str(root / "scripts/evaluate_triage_endpoint.py"),
                    "--url",
                    "http://127.0.0.1:8000",
                    "--scenarios",
                    str(args.scenarios),
                    "--output",
                    str(directory / "endpoint.json"),
                ],
                env=stage_env,
                timeout=1800,
            )
            audit = subprocess.run(
                [
                    str(args.api_python),
                    str(root / "scripts/verify_endpoint_audit.py"),
                    "--report",
                    str(directory / "endpoint.json"),
                    "--audit",
                    str(directory / "audit.jsonl"),
                    "--output",
                    str(directory / "audit-proof.json"),
                ],
                env=stage_env,
                timeout=60,
            )
            reports[stage] = {
                "measurement_exit_code": measure.returncode,
                "audit_exit_code": audit.returncode,
            }
            stop_owned(api_process)
            api_process = None
        (args.output / "summary.json").write_text(
            json.dumps(
                {
                    "status": "measurement_completed",
                    "reports": reports,
                    "optimizer_steps": 0,
                    "test_records_used": 0,
                    "public_endpoint": False,
                    "clinical_validation": False,
                    "limits": [
                        "Loopback GPU integration, not an externally accessible cloud deployment.",
                        "Structured FP16 serving differs from raw FP4 v28 generation.",
                    ],
                },
                indent=2,
            )
        )
    finally:
        stop_owned(api_process)
        stop_owned(model_process)


if __name__ == "__main__":
    main()
