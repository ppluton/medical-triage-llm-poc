#!/usr/bin/env python3
"""Measure an explicitly selected private endpoint using synthetic scenarios only."""

import argparse
import json
import math
import os
import time
from pathlib import Path
from urllib.parse import urlparse
from uuid import UUID

import httpx

from triage_poc.api import TriageRequest, TriageResponse


def evaluate(client, scenarios):
    """Keep failures in the report; never log credentials or transport exceptions."""
    if not scenarios or any(row.get("synthetic") is not True for row in scenarios):
        raise ValueError("Non-empty explicitly synthetic scenarios required")
    requests = [TriageRequest.model_validate(row["request"]) for row in scenarios]
    records, seen = [], set()
    for row, request in zip(scenarios, requests, strict=True):
        result = {"id": row["id"], "success": False}
        started = time.perf_counter()
        try:
            response = client.post("/v1/triage", json=request.model_dump())
            result["http_status"] = response.status_code
            response.raise_for_status()
            parsed = TriageResponse.model_validate_json(response.text)
            identifier = str(UUID(parsed.interaction_id))
            if identifier in seen or not parsed.safety_notice.strip() or not parsed.model_version:
                raise ValueError("Missing or duplicate trace metadata")
            seen.add(identifier)
            result.update(success=True, response=parsed.model_dump())
        except (httpx.HTTPError, ValueError):
            result["error"] = "transport_http_or_response_contract_failure"
        result["client_latency_ms"] = round((time.perf_counter() - started) * 1000, 2)
        records.append(result)
    latencies = sorted(r["client_latency_ms"] for r in records)
    successes = sum(r["success"] for r in records)
    return {
        "records": records,
        "requests": len(records),
        "successes": successes,
        "failures": len(records) - successes,
        "error_rate": (len(records) - successes) / len(records),
        "latency_population": "all requests including failures, serial, cold start included",
        "percentile_method": "nearest_rank",
        "client_p50_ms": latencies[math.ceil(len(latencies) * 0.5) - 1],
        "client_p95_ms": latencies[math.ceil(len(latencies) * 0.95) - 1],
        "clinical_validation": "not_performed",
        "limits": [
            "Response IDs do not prove persistence in server audit logs.",
            "This is not a concurrent load test or clinical quality score.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True, help="Server origin, e.g. https://private.example")
    parser.add_argument("--scenarios", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    parsed = urlparse(args.url)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
        or (parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1"})
    ):
        raise ValueError("Use an HTTPS origin or local HTTP origin without credentials")
    if args.output.exists():
        raise ValueError("Fresh report path required")
    token = os.environ.get("TRIAGE_API_TOKEN")
    if not token:
        raise ValueError("TRIAGE_API_TOKEN is required")
    scenarios = json.loads(args.scenarios.read_text())
    with httpx.Client(
        base_url=args.url,
        headers={"Authorization": "Bearer " + token},
        timeout=90,
        follow_redirects=False,
    ) as client:
        report = evaluate(client, scenarios)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: report[k]
                for k in ["requests", "successes", "failures", "client_p50_ms", "client_p95_ms"]
            }
        )
    )
    raise SystemExit(1 if report["failures"] else 0)


if __name__ == "__main__":
    main()
