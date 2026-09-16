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


def test_provider_transport_and_persisted_audit_use_redacted_context(tmp_path):
    def handler(request):
        assert b"alice@example.org" not in request.content
        assert b"EMAIL_ADDRESS" in request.content
        assert json.loads(request.content)["response_format"]["type"] == "json_schema"
        from triage_poc.triage_probe import messages_for_scenario
        from triage_poc.triage_prompt import PROMPT_VERSION

        assert json.loads(request.content)["messages"][0] == messages_for_scenario(
            {"request": BODY}
        )[0]
        assert PROMPT_VERSION == "triage-demo-v6-proposed"

        return httpx.Response(200, json={"choices": [{"finish_reason": "stop", "message": {
            "content": json.dumps({**RESULT, "summary": "Contact alice@example.org"})}}]})
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
    assert "alice@example.org" not in audit.read_text()
    assert "alice@example.org" not in response.text
    assert record["anonymized_input"]["patient_context"]["symptoms"] == [
        "synthetic contact: <EMAIL_ADDRESS>"
    ]
    assert record["output"] == response.json()
    assert record["output"]["summary"] == "Contact <EMAIL_ADDRESS>"
    assert record["guardrail_status"] == "model_output"
    assert record["guardrail_version"] == "proposed-guardrails-v2"
    assert record["guardrail_reasons"] == []


def test_provider_replaces_unsupported_stability_with_audited_safe_fallback(tmp_path):
    body = {"language": "en", "patient_context": {
        "age_group": "unknown", "symptoms": ["I do not feel well."], "vitals": {}}}
    hallucinated = {
        "triage_level": "deferred",
        "summary": "The patient is stable and has no warning signs.",
        "clinical_rationale": ["Vital signs are stable."],
        "missing_information": [],
    }
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(
        200,
        json={"choices": [{"finish_reason": "stop", "message": {
            "content": json.dumps(hallucinated)}}]},
    ))) as transport:
        provider = VllmProvider(
            "http://localhost:8001/v1", "sft", "fixture",
            anonymizer=Redactor(), client=transport,
        )
        audit = tmp_path / "audit.jsonl"
        response = TestClient(create_app(provider, JsonlAudit(audit))).post(
            "/v1/triage", json=body
        )
    assert response.status_code == 200
    assert response.json()["triage_level"] == "moderate"
    assert "stable" not in response.json()["summary"].lower()
    record = json.loads(audit.read_text())
    assert record["guardrail_status"] == "safe_fallback"
    assert set(record["guardrail_reasons"]) == {
        "invented_vital_stability",
        "invented_stability_or_absence",
        "explicit_uncertainty_or_vulnerability",
    }


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
    from triage_poc.api import ModelResult, ProviderResult
    from triage_poc.serving import create_serving_app

    calls = []

    class Provider:
        prompt_version = "synthetic"

        def __init__(self, *args):
            pass

        def triage(self, request):
            calls.append(request)
            return ProviderResult(result=ModelResult.model_validate(RESULT),
                                  model_version="synthetic-model", anonymized_input=request)

    monkeypatch.setattr("triage_poc.serving.VllmProvider", Provider)
    for key, value in {"TRIAGE_API_TOKEN": "x" * 32, "TRIAGE_VLLM_URL": "http://vllm/v1",
                       "TRIAGE_MODEL_NAME": "synthetic", "TRIAGE_MODEL_VERSION": "synthetic",
                       "TRIAGE_AUDIT_PATH": str(tmp_path / "audit.jsonl")}.items():
        monkeypatch.setenv(key, value)
    client = TestClient(create_serving_app())
    demo = client.get("/demo/")
    assert demo.status_code == 200
    assert "TRIAGE_API_TOKEN" not in demo.text
    assert demo.headers["cache-control"] == "no-store"
    assert "frame-ancestors 'none'" in demo.headers["content-security-policy"]
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200
    assert client.post("/v1/triage", json=BODY).status_code == 401
    assert client.get("/healthz").status_code == 401
    assert not calls and not (tmp_path / "audit.jsonl").exists()
    response = client.post("/v1/triage", json=BODY,
                           headers={"Authorization": "Bearer " + "x" * 32})
    assert response.status_code == 200
    assert len(calls) == 1
    assert len((tmp_path / "audit.jsonl").read_text().splitlines()) == 1


def test_jsonl_audit_can_sync_its_volume_parent(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(
        "triage_poc.serving.subprocess.run",
        lambda command, **kwargs: calls.append((command, kwargs)),
    )
    audit = JsonlAudit(tmp_path / "audit/interactions.jsonl", sync_parent=True)
    audit.write({"synthetic": True})
    assert calls == [
        (["sync", str(tmp_path / "audit")], {"check": True, "timeout": 10})
    ]


def test_failed_output_privacy_check_keeps_audit_content_free(tmp_path):
    class OutputBlocked(Redactor):
        def anonymize(self, text, language):
            if text == "Synthetic example.":
                return SimpleNamespace(text=text, audit=SimpleNamespace(status="review_required"))
            return super().anonymize(text, language)

    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(
        200, json={"choices": [{"finish_reason": "stop", "message": {
            "content": json.dumps(RESULT)}}]}
    ))) as transport:
        provider = VllmProvider("http://localhost:8001/v1", "sft", "fixture",
                                anonymizer=OutputBlocked(), client=transport)
        path = tmp_path / "audit.jsonl"
        response = TestClient(create_app(provider, JsonlAudit(path))).post("/v1/triage", json=BODY)
    assert response.status_code == 502
    record = json.loads(path.read_text())
    assert record["status"] == "provider_or_schema_failure"
    assert "output" not in record and "anonymized_input" not in record
    assert "alice@example.org" not in path.read_text()
    assert "Synthetic example." not in response.text


def test_successful_inference_is_withheld_when_audit_write_fails():
    class BrokenAudit:
        def write(self, record):
            raise OSError("sensitive storage failure")

    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(
        200, json={"choices": [{"finish_reason": "stop", "message": {
            "content": json.dumps(RESULT)}}]}
    ))) as transport:
        provider = VllmProvider("http://localhost:8001/v1", "sft", "fixture",
                                anonymizer=Redactor(), client=transport)
        response = TestClient(create_app(provider, BrokenAudit())).post("/v1/triage", json=BODY)
    assert response.status_code == 503
    assert "Audit unavailable" in response.json()["detail"]
    assert "sensitive storage" not in response.text
    assert "Synthetic example." not in response.text


@pytest.mark.parametrize(('reply', 'code'), [
    ({'finish_reason': 'length', 'message': {'content': 'private fixture'}},
     'generation_length'),
    ({'finish_reason': 'stop', 'message': {'content': 'private fixture'}},
     'output_contract'),
    ({}, 'generation_incomplete'),
])
def test_failure_audit_contains_only_bounded_category(tmp_path, reply, code):
    with httpx.Client(transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json={'choices': [reply]}))) as transport:
        provider = VllmProvider('http://localhost:8001/v1', 'sft', 'fixture',
                                anonymizer=Redactor(), client=transport)
        audit = tmp_path / 'audit.jsonl'
        response = TestClient(create_app(provider, JsonlAudit(audit))).post('/v1/triage', json=BODY)
    assert response.status_code == 502
    record = json.loads(audit.read_text())
    assert record['failure_code'] == code
    assert 'output' not in record and 'anonymized_input' not in record
    assert 'private fixture' not in audit.read_text() + response.text
    assert 'alice@example.org' not in audit.read_text() + response.text
