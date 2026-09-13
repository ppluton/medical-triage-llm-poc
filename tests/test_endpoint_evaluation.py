import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest

spec = importlib.util.spec_from_file_location(
    "endpoint_eval", "scripts/evaluate_triage_endpoint.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_endpoint_evaluation_counts_failures_and_reused_interaction_ids(monkeypatch):
    ticks = iter([0, 1, 3, 4, 7, 8, 10, 12])
    monkeypatch.setattr(module, "time", SimpleNamespace(perf_counter=lambda: next(ticks)))
    scenarios = json.loads(Path("data/samples/synthetic-triage-development-v2.json").read_text())[
        :3
    ]
    interaction_id = str(uuid4())
    calls = []

    def respond(request):
        calls.append(request)
        if len(calls) == 3:
            return httpx.Response(502, json={"detail": "Do not include this error body"})
        return httpx.Response(
            200,
            json={
                "triage_level": "moderate",
                "summary": "Synthetic",
                "clinical_rationale": ["Synthetic"],
                "missing_information": [],
                "interaction_id": interaction_id,
                "safety_notice": "Professional review required",
                "model_version": "fixture",
                "latency_ms": 1,
            },
        )

    with httpx.Client(
        base_url="https://synthetic.example", transport=httpx.MockTransport(respond)
    ) as client:
        result = module.evaluate(client, scenarios)
    assert result["successes"] == 1
    assert result["failures"] == 2
    assert result["requests"] == 3
    assert result["elapsed_seconds"] == 12
    assert result["requests_per_second"] == pytest.approx(3 / 12)
    assert result["successful_responses_per_second"] == pytest.approx(1 / 12)
    assert result["concurrency"] == 1
    assert result["client_p95_ms"] >= result["client_p50_ms"]
    assert "Do not include" not in json.dumps(result)
    assert all(request.url.path == "/v1/triage" for request in calls)


def test_endpoint_evaluation_refuses_unmarked_data_before_network():
    with pytest.raises(ValueError, match="synthetic"):
        module.evaluate(None, [{"synthetic": False}])
