"""Synthetic multi-turn collection and privacy contract checks."""

import json
from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient

from triage_poc.api import ModelResult, ProviderResult, create_app
from triage_poc.serving import JsonlAudit, VllmProvider

RESULT = dict(
    triage_level="maximum",
    summary="Synthetic fixture, not medical advice.",
    clinical_rationale=["Synthetic only."],
    missing_information=[],
)


class Provider:
    def triage(self, request):
        return ProviderResult(
            result=ModelResult(**RESULT), model_version="synthetic", anonymized_input=request
        )


@pytest.mark.parametrize("language", ["fr", "en"])
def test_collection_advances_without_repeating_answers_or_delaying_priority(tmp_path, language):
    path = tmp_path / "audit.jsonl"
    client = TestClient(create_app(Provider(), JsonlAudit(path)))
    context = {"age_group": "adult", "symptoms": ["synthetic"]}

    def submit():
        response = client.post(
            "/v1/triage", json={"language": language, "patient_context": context}
        )
        assert response.status_code == 200
        assert response.json()["triage_level"] == "maximum"
        return response.json()

    first = submit()
    assert [q["field"] for q in first["collection"]["questions"]] == ["duration", "evolution"]
    assert first["collection"]["questions"][0]["text"] == (
        "Depuis quand les symptômes sont-ils présents ?"
        if language == "fr"
        else "When did the symptoms start?"
    )
    context.update(duration="Synthetic duration", evolution="Synthetic evolution")
    second = submit()
    assert [q["field"] for q in second["collection"]["questions"]] == [
        "intensity",
        "associated_symptoms",
    ]
    context.update(
        intensity="Synthetic intensity",
        confirmed_absent=[
            "associated_symptoms",
            "medical_history",
            "allergies",
            "medications",
            "vulnerability_factors",
        ],
        unavailable_fields=["vitals"],
    )
    third = submit()
    assert third["collection"]["questions"] == []
    assert third["collection"]["pending_fields"] == []
    assert third["collection"]["unavailable_fields"] == ["vitals"]
    records = [json.loads(line) for line in path.read_text().splitlines()]
    assert [record["output"] for record in records] == [first, second, third]
    assert len({r["interaction_id"] for r in records}) == 3


@pytest.mark.parametrize(
    "extra",
    [
        {"duration": "Synthetic", "unavailable_fields": ["duration"]},
        {"allergies": ["Synthetic"], "confirmed_absent": ["allergies"]},
        {"confirmed_absent": ["allergies"], "unavailable_fields": ["allergies"]},
        {"unavailable_fields": ["duration", "duration"]},
        {"confirmed_absent": ["duration"]},
        {"unavailable_fields": ["patient_name"]},
    ],
)
def test_inconsistent_or_unbounded_status_rejected(extra):
    body = {
        "language": "fr",
        "patient_context": {"age_group": "adult", "symptoms": ["synthetic"], **extra},
    }
    assert TestClient(create_app(Provider())).post("/v1/triage", json=body).status_code == 422


def test_empty_vitals_and_unknown_age_remain_unanswered():
    body = {
        "language": "en",
        "patient_context": {
            "age_group": "unknown",
            "symptoms": ["synthetic"],
            "vitals": {"heart_rate": None},
        },
    }
    progress = TestClient(create_app(Provider())).post("/v1/triage", json=body).json()["collection"]
    assert "age_group" in progress["pending_fields"]
    assert "vitals" in progress["pending_fields"]
    assert "allergies" in progress["pending_fields"]


def test_new_free_text_fields_are_redacted_before_transport_and_audit(tmp_path):
    marker = "synthetic@example.org"

    class Redactor:
        def anonymize(self, text, language):
            return SimpleNamespace(
                text=text.replace(marker, "<EMAIL_ADDRESS>"), audit=SimpleNamespace(status="passed")
            )

    def handler(request):
        payload = json.loads(request.content)
        context = json.loads(payload["messages"][1]["content"])["patient_context"]
        assert marker not in request.content.decode()
        assert context["evolution"] == "<EMAIL_ADDRESS>"
        assert context["intensity"] == "<EMAIL_ADDRESS>"
        assert context["associated_symptoms"] == ["<EMAIL_ADDRESS>"]
        assert context["vulnerability_factors"] == ["<EMAIL_ADDRESS>"]
        return httpx.Response(
            200,
            json={
                "choices": [{"finish_reason": "stop", "message": {"content": json.dumps(RESULT)}}]
            },
        )

    path = tmp_path / "audit.jsonl"
    with httpx.Client(transport=httpx.MockTransport(handler)) as transport:
        provider = VllmProvider(
            "http://localhost:8001/v1", "sft", "synthetic", anonymizer=Redactor(), client=transport
        )
        body = {
            "language": "en",
            "patient_context": {
                "age_group": "adult",
                "symptoms": ["synthetic"],
                "evolution": marker,
                "intensity": marker,
                "associated_symptoms": [marker],
                "vulnerability_factors": [marker],
            },
        }
        response = TestClient(create_app(provider, JsonlAudit(path))).post("/v1/triage", json=body)
    assert response.status_code == 200
    assert marker not in path.read_text() + response.text
    assert "<EMAIL_ADDRESS>" in path.read_text()
