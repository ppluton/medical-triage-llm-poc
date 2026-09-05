import json
from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient

from triage_poc.api import create_app
from triage_poc.serving import JsonlAudit, VllmProvider

BODY = {"language": "en", "patient_context": {
    "age_group": "adult", "symptoms": ["synthetic contact: alice@example.org"],
    "vitals": {"heart_rate": 80}}}
RESULT = {"triage_level": "moderate", "summary": "Synthetic example.",
          "clinical_rationale": ["Professional review required."],
          "missing_information": ["Duration"], "follow_up_questions": ["When did it begin?"]}


class Redactor:
    def anonymize(self, text, language):
        return SimpleNamespace(text=text.replace("alice@example.org", "<EMAIL_ADDRESS>"),
                               audit=SimpleNamespace(status="passed"))


def test_provider_transport_receives_redacted_context_and_audit_is_text_free(tmp_path):
    def handler(request):
        assert b"alice@example.org" not in request.content
        assert b"EMAIL_ADDRESS" in request.content
        assert json.loads(request.content)["response_format"]["type"] == "json_schema"
        return httpx.Response(200, json={"choices": [{"finish_reason": "stop", "message": {
            "content": json.dumps(RESULT)}}]})
    with httpx.Client(transport=httpx.MockTransport(handler)) as transport:
        provider = VllmProvider("http://localhost:8001/v1", "sft", "sha256:fixture",
                                anonymizer=Redactor(), client=transport)
        audit = tmp_path / "audit.jsonl"
        response = TestClient(create_app(provider, JsonlAudit(audit))).post("/v1/triage", json=BODY)
    assert response.status_code == 200
    assert response.json()["follow_up_questions"] == ["When did it begin?"]
    assert "healthcare professional" in response.json()["safety_notice"]
    assert response.json()["latency_ms"] >= 0
    record = json.loads(audit.read_text())
    assert record["interaction_id"] == response.json()["interaction_id"]
    assert "alice" not in audit.read_text() and "symptoms" not in record


@pytest.mark.parametrize("reply", [
    {"finish_reason": "length", "message": {"content": json.dumps(RESULT)}},
    {"finish_reason": "stop", "message": {"content": '{"triage_level":"invalid"}'}},
])
def test_rejects_truncated_or_invalid_provider_output(reply):
    with httpx.Client(transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json={"choices": [reply]}))) as transport:
        provider = VllmProvider("http://localhost:8001/v1", "sft", "fixture",
                                anonymizer=Redactor(), client=transport)
        response = TestClient(create_app(provider)).post("/v1/triage", json=BODY)
    assert response.status_code == 502
    assert "healthcare professional" in response.json()["detail"]


def test_failed_privacy_check_prevents_network_call():
    class Blocked:
        def anonymize(self, *args):
            raise RuntimeError("sensitive internal failure")
    provider = VllmProvider("http://localhost:8001/v1", "sft", "fixture", anonymizer=Blocked())
    response = TestClient(create_app(provider)).post("/v1/triage", json=BODY)
    assert response.status_code == 502
    assert "sensitive" not in response.text


def test_audit_failure_does_not_deliver_assessment():
    class BrokenAudit:
        def write(self, record):
            raise OSError("disk full")
    response = TestClient(create_app(audit=BrokenAudit())).post("/v1/triage", json=BODY)
    assert response.status_code == 503
    assert "Audit unavailable" in response.json()["detail"]


def test_blank_and_extra_fields_rejected():
    client = TestClient(create_app())
    for context in [{"age_group": "adult", "symptoms": ["   "]},
                    {"age_group": "adult", "symptoms": ["synthetic"], "ignored": True}]:
        assert client.post("/v1/triage", json={"language": "fr",
                                              "patient_context": context}).status_code == 422


def test_private_factory_authenticates_before_provider_or_audit(monkeypatch, tmp_path):
    from triage_poc.api import ModelResult
    from triage_poc.serving import create_serving_app

    calls = []

    class Provider:
        prompt_version = "synthetic"

        def __init__(self, *args):
            pass

        def triage(self, request):
            calls.append(request)
            return ModelResult.model_validate(RESULT), "synthetic-model"

    monkeypatch.setattr("triage_poc.serving.VllmProvider", Provider)
    for key, value in {"TRIAGE_API_TOKEN": "x" * 32, "TRIAGE_VLLM_URL": "http://vllm/v1",
                       "TRIAGE_MODEL_NAME": "synthetic", "TRIAGE_MODEL_VERSION": "synthetic",
                       "TRIAGE_AUDIT_PATH": str(tmp_path / "audit.jsonl")}.items():
        monkeypatch.setenv(key, value)
    client = TestClient(create_serving_app())
    assert client.post("/v1/triage", json=BODY).status_code == 401
    assert client.get("/healthz").status_code == 401
    assert not calls and not (tmp_path / "audit.jsonl").exists()
    response = client.post("/v1/triage", json=BODY,
                           headers={"Authorization": "Bearer " + "x" * 32})
    assert response.status_code == 200
    assert len(calls) == 1
    assert len((tmp_path / "audit.jsonl").read_text().splitlines()) == 1
