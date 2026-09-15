"""Synthetic audit persistence across independent API processes."""
import json
import os
import subprocess
import sys

from fastapi.testclient import TestClient

from triage_poc.api import ModelResult, ProviderResult, create_app
from triage_poc.serving import JsonlAudit

BODY = {"language": "en", "patient_context": {"age_group": "adult", "symptoms": ["synthetic"]}}


class Provider:
    def triage(self, request):
        return ProviderResult(
            result=ModelResult(triage_level="moderate", summary="Synthetic fixture",
                               clinical_rationale=["Synthetic"], missing_information=[]),
            model_version="synthetic", anonymized_input=request)


def test_sync_failure_prevents_assessment_delivery(monkeypatch, tmp_path):
    def fail_sync(descriptor):
        raise OSError("Synthetic disk sync failure")
    monkeypatch.setattr(os, "fsync", fail_sync)
    response = TestClient(create_app(Provider(), JsonlAudit(tmp_path / "audit.jsonl"))).post(
        "/v1/triage", json=BODY)
    assert response.status_code == 503
    assert "Audit unavailable" in response.json()["detail"]
    assert "triage_level" not in response.json()


def test_new_api_process_appends_without_losing_prior_interaction(tmp_path):
    program = '''
import json, sys
from pathlib import Path
from fastapi.testclient import TestClient
from triage_poc.api import ModelResult, ProviderResult, create_app
from triage_poc.serving import JsonlAudit
class Provider:
    def triage(self, request):
        return ProviderResult(result=ModelResult(
            triage_level="moderate", summary="Synthetic fixture",
            clinical_rationale=["Synthetic"], missing_information=[]),
            model_version="synthetic", anonymized_input=request)
with TestClient(create_app(Provider(), JsonlAudit(Path(sys.argv[1])))) as client:
    response = client.post("/v1/triage", json={"language":"en", "patient_context":{
        "age_group":"adult", "symptoms":["synthetic"]}})
    assert response.status_code == 200
    print(json.dumps(response.json()))
'''
    path = tmp_path / "audit.jsonl"
    responses = []
    for _ in range(2):
        result = subprocess.run([sys.executable, "-c", program, str(path)],
                                capture_output=True, text=True, timeout=60, check=True)
        responses.append(json.loads(result.stdout))
    records = [json.loads(line) for line in path.read_text().splitlines()]
    assert len(records) == 2
    assert records[0]["interaction_id"] != records[1]["interaction_id"]
    assert [record["output"] for record in records] == responses
    assert path.stat().st_mode & 0o777 == 0o600
