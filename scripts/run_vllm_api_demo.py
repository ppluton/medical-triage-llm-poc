#!/usr/bin/env python3
"""Run a loopback-only real-model API demonstration and preserve failed measurements."""

import argparse
import ctypes
import hashlib
import json
import os
import re
import secrets
import signal
import subprocess
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

from triage_poc.model_snapshot import (
    BASE_SERVED_MODEL_NAME,
    EXPECTED_BASE_REVISION,
    verify_base_snapshot,
)

EXPECTED_GUARDRAIL_VERSION = "proposed-guardrails-v1"
GUARDRAIL_STATUSES = frozenset({"model_output", "corrected", "safe_fallback"})


def summarize_guardrail_audit(report_path, audit_path):
    """Summarize versioned guardrail decisions without copying patient text."""
    report = json.loads(Path(report_path).read_text())
    audit = [
        json.loads(line) for line in Path(audit_path).read_text().splitlines() if line.strip()
    ]
    successful = [record for record in report["records"] if record.get("success") is True]
    expected_ids = [record["response"]["interaction_id"] for record in successful]
    audit_by_id = {}
    for row in audit:
        audit_by_id.setdefault(row.get("interaction_id"), []).append(row)
    statuses = Counter()
    reasons = Counter()
    issue_counts = Counter()
    for interaction_id in expected_ids:
        rows = audit_by_id.get(interaction_id, [])
        if len(rows) != 1:
            issue_counts["missing_or_duplicate_audit_entry"] += 1
            continue
        row = rows[0]
        status = row.get("guardrail_status")
        version = row.get("guardrail_version")
        row_reasons = row.get("guardrail_reasons")
        if status not in GUARDRAIL_STATUSES:
            issue_counts["invalid_guardrail_status"] += 1
            continue
        if version != EXPECTED_GUARDRAIL_VERSION:
            issue_counts["unexpected_guardrail_version"] += 1
        if not isinstance(row_reasons, list) or any(
            not isinstance(reason, str) or not re.fullmatch(r"[a-z0-9_]+", reason)
            for reason in row_reasons
        ):
            issue_counts["invalid_guardrail_reasons"] += 1
            continue
        statuses[status] += 1
        reasons.update(row_reasons)
    result = {
        "status": "passed" if successful and not issue_counts else "failed",
        "successful_responses": len(successful),
        "guardrail_version": EXPECTED_GUARDRAIL_VERSION,
        "guardrail_status_counts": dict(sorted(statuses.items())),
        "guardrail_reason_counts": dict(sorted(reasons.items())),
        "issue_counts": dict(sorted(issue_counts.items())),
    }
    return result


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
    for name in (
        "vllm-python",
        "api-python",
        "base-model",
        "sft",
        "dpo",
        "output",
        "scenarios",
    ):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--collection-scenarios", type=Path)
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
    base_snapshot = verify_base_snapshot(args.base_model)
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
    variants = {
        "base": (BASE_SERVED_MODEL_NAME, EXPECTED_BASE_REVISION),
        "sft": ("chsa-sft", expected["sft"]),
        "dpo": ("chsa-dpo", expected["dpo"]),
    }
    try:
        command = [
            str(args.vllm_python),
            "-m",
            "vllm.entrypoints.openai.api_server",
            "--model",
            str(args.base_model),
            "--served-model-name",
            BASE_SERVED_MODEL_NAME,
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
        if not {item[0] for item in variants.values()} <= {
            model["id"] for model in models["data"]
        }:
            raise ValueError("Expected base and LoRA models are not served")
        for stage, (model_name, model_version) in variants.items():
            directory = args.output / stage
            directory.mkdir()
            stage_env = dict(
                env,
                TRIAGE_API_TOKEN=token,
                TRIAGE_VLLM_URL="http://127.0.0.1:8001/v1",
                TRIAGE_MODEL_NAME=model_name,
                TRIAGE_MODEL_VERSION=model_version,
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
            endpoint_guardrails = summarize_guardrail_audit(
                directory / "endpoint.json", directory / "audit.jsonl"
            )
            (directory / "endpoint-guardrails.json").write_text(
                json.dumps(endpoint_guardrails, indent=2) + "\n"
            )
            reports[stage]["endpoint_guardrails"] = endpoint_guardrails
            if args.collection_scenarios:
                collection = subprocess.run(
                    [str(args.api_python), str(root / "scripts/evaluate_collection_endpoint.py"),
                     "--scenarios", str(args.collection_scenarios),
                     "--output", str(directory / "collection.json")],
                    env=stage_env, timeout=1800,
                )
                collection_audit = subprocess.run(
                    [str(args.api_python), str(root / "scripts/verify_endpoint_audit.py"),
                     "--report", str(directory / "collection.json"),
                     "--audit", str(directory / "audit.jsonl"),
                     "--output", str(directory / "collection-audit-proof.json")],
                    env=stage_env, timeout=60,
                )
                reports[stage].update(collection_exit_code=collection.returncode,
                                      collection_audit_exit_code=collection_audit.returncode)
                collection_guardrails = summarize_guardrail_audit(
                    directory / "collection.json", directory / "audit.jsonl"
                )
                (directory / "collection-guardrails.json").write_text(
                    json.dumps(collection_guardrails, indent=2) + "\n"
                )
                reports[stage]["collection_guardrails"] = collection_guardrails
            stop_owned(api_process)
            api_process = None
        (args.output / "summary.json").write_text(
            json.dumps(
                {
                    "status": "measurement_completed",
                    "reports": reports,
                    "variant_order": list(variants),
                    "scenario_sha256": hashlib.sha256(args.scenarios.read_bytes()).hexdigest(),
                    "collection_scenario_sha256": (
                        hashlib.sha256(args.collection_scenarios.read_bytes()).hexdigest()
                        if args.collection_scenarios else None),
                    "base_snapshot": base_snapshot,
                    "huggingface_model_download": False,
                    "optimizer_steps": 0,
                    "test_records_used": 0,
                    "public_endpoint": False,
                    "clinical_validation": False,
                    "limits": [
                        "Loopback GPU integration, not an externally accessible cloud deployment.",
                        "Structured FP16 serving differs from raw FP4 v28 generation.",
                        "Serial Base/SFT/DPO latency is confounded by warmup and cache effects.",
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
