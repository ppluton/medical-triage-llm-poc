from fastapi.testclient import TestClient

from triage_poc.api import ModelResult, TriageRequest, create_app


class FakeProvider:
    def triage(self, request: TriageRequest):
        return (
            ModelResult(
                triage_level="moderate",
                summary="Synthetic fixture.",
                clinical_rationale=["Synthetic only."],
                missing_information=["Vitals"],
            ),
            "fake-model-v1",
        )


def test_triage_contract_returns_required_safety_notice():
    response = TestClient(create_app(FakeProvider())).post(
        "/v1/triage",
        json={
            "language": "fr",
            "patient_context": {"age_group": "adult", "symptoms": ["synthetic"]},
        },
    )
    assert response.status_code == 200
    assert response.json()["triage_level"] == "moderate"
    assert "ne remplace pas" in response.json()["safety_notice"]


def test_triage_rejects_empty_symptoms_and_unconfigured_model():
    client = TestClient(create_app())
    invalid = client.post(
        "/v1/triage",
        json={"language": "fr", "patient_context": {"age_group": "adult", "symptoms": []}},
    )
    assert invalid.status_code == 422
    valid = client.post(
        "/v1/triage",
        json={
            "language": "fr",
            "patient_context": {"age_group": "adult", "symptoms": ["synthetic"]},
        },
    )
    assert valid.status_code == 503
