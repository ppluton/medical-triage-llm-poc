"""Synthetic protocol tests for the driver of API collection turns."""
import copy
import json
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from triage_poc.api import ModelResult, ProviderResult, create_app
from triage_poc.dialogue_evaluation import evaluate_dialogue
from triage_poc.serving import JsonlAudit

SCENARIOS = json.loads(Path("data/samples/synthetic-collection-dialogues-v1.json").read_text())


class Provider:
    def triage(self, request):
        return ProviderResult(result=ModelResult(
            triage_level="moderate", summary="Synthetic fixture", clinical_rationale=["Synthetic"],
            missing_information=[]), model_version="synthetic", anonymized_input=request)


@pytest.mark.parametrize("scenario", SCENARIOS, ids=["fr", "en"])
def test_driver_completes_questions_returned_by_api_and_preserves_context(tmp_path, scenario):
    path = tmp_path / "audit.jsonl"
    with TestClient(create_app(Provider(), JsonlAudit(path))) as client:
        result = evaluate_dialogue(client, scenario)
    assert result["status"] == "passed"
    assert len(result["records"]) == 6
    assert result["unanswered_fields"] == []
    audit = [json.loads(line) for line in path.read_text().splitlines()]
    assert [row["output"] for row in audit] == [r["response"] for r in result["records"]]
    assert all(row["anonymized_input"]["patient_context"]["symptoms"] ==
               scenario["request"]["patient_context"]["symptoms"] for row in audit)
    last = audit[-1]["anonymized_input"]["patient_context"]
    assert last["duration"] == scenario["answers"]["duration"]["value"]
    assert last["confirmed_absent"] == ["associated_symptoms"]
    assert set(last["unavailable_fields"]) == {
        "medical_history", "allergies", "medications", "vulnerability_factors", "vitals"}


def test_driver_rejects_repeated_questions_even_if_http_succeeds():
    with TestClient(create_app(Provider())) as client:
        first = client.post("/v1/triage", json=SCENARIOS[0]["request"]).json()
    calls = []
    def reply(request):
        calls.append(request)
        response = copy.deepcopy(first)
        from uuid import uuid4
        response["interaction_id"] = str(uuid4())
        return httpx.Response(200, json=response)
    with httpx.Client(base_url="https://synthetic.example",
                      transport=httpx.MockTransport(reply)) as client:
        result = evaluate_dialogue(client, SCENARIOS[0])
    assert result["status"] == "failed"
    assert len(calls) == 2
    assert result["issues"][0]["code"] == "collection_progress_mismatch"


def test_driver_keeps_http_failure_without_copying_private_error_body():
    with httpx.Client(base_url="https://synthetic.example", transport=httpx.MockTransport(
            lambda request: httpx.Response(502, text="synthetic private error"))) as client:
        result = evaluate_dialogue(client, SCENARIOS[0])
    assert result["status"] == "failed"
    assert result["records"][0]["success"] is False
    assert "synthetic private error" not in json.dumps(result)


@pytest.mark.parametrize("mutation", ["not_synthetic", "invalid_answer"])
def test_fixture_rejected_before_network(mutation):
    scenario = copy.deepcopy(SCENARIOS[0])
    if mutation == "not_synthetic":
        scenario["synthetic"] = False
    else:
        scenario["answers"]["duration"] = {"status": "value", "value": ""}
    with pytest.raises(ValueError):
        evaluate_dialogue(None, scenario)
