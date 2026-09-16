from fastapi.testclient import TestClient

from triage_poc.api import API_VERSION, ModelResult, ProviderResult, TriageRequest, create_app


class FakeProvider:
    def triage(self, request: TriageRequest):
        return ProviderResult(
            result=ModelResult(
                triage_level="moderate",
                summary="Synthetic fixture.",
                clinical_rationale=["Synthetic only."],
                missing_information=["Vitals"],
            ),
            model_version="fake-model-v1", anonymized_input=request,
        )


def test_openapi_exposes_current_api_version():
    response = TestClient(create_app(FakeProvider())).get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["version"] == API_VERSION == "0.4.0"


def test_demo_ui_is_packaged_and_redirected_without_external_assets():
    client = TestClient(create_app(FakeProvider()))
    redirect = client.get("/", follow_redirects=False)
    page = client.get("/demo/")
    script = client.get("/demo/app.js")

    assert redirect.status_code == 307 and redirect.headers["location"] == "/demo/"
    assert page.status_code == 200
    assert "POC pédagogique" in page.text
    assert "aucune donnée patient réelle" in page.text
    assert 'id="follow-up-form"' in page.text
    assert "http://" not in page.text and "https://" not in page.text
    assert script.status_code == 200
    assert 'fetch("/v1/triage"' in script.text
    assert "data.collection.questions" in script.text
    assert "structuredClone(currentContext)" in script.text
    assert "localStorage" not in script.text and "sessionStorage" not in script.text


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
