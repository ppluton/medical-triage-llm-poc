import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "endpoint_audit", Path("scripts/verify_endpoint_audit.py")
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_reconciliation_requires_exact_unique_persisted_response_and_versions():
    response = {"interaction_id": "synthetic-1", "summary": "Synthetic output"}
    record = {"id": "synthetic-case", "success": True, "response": response}
    report = {"records": [record]}
    audit = {"interaction_id": "synthetic-1", "output": response,
             "anonymized_input": {"synthetic": True}, "privacy_status": "passed",
             "prompt_version": "fixture", "controls_version": "fixture"}
    assert module.reconcile(report, [audit])["status"] == "passed"
    assert module.reconcile(report, [audit, audit])["status"] == "failed"
    assert module.reconcile(report, [])["status"] == "failed"
    for changes in ({"output": {**response, "summary": "Different"}},
                    {"privacy_status": "review_required"}, {"prompt_version": ""}):
        assert module.reconcile(report, [{**audit, **changes}])["status"] == "failed"
    assert module.reconcile({"records": [record, record]}, [audit])["status"] == "failed"
    assert module.reconcile({"records": [{"success": False}]}, [audit])["status"] == "failed"


def test_reconcile_real_fastapi_response_with_written_jsonl(tmp_path):
    import json

    from fastapi.testclient import TestClient

    from triage_poc.api import ModelResult, ProviderResult, create_app
    from triage_poc.serving import JsonlAudit

    class SyntheticProvider:
        prompt_version = "synthetic-fixture"

        def triage(self, request):
            return ProviderResult(
                result=ModelResult(triage_level="moderate", summary="Synthetic example",
                                   clinical_rationale=["Synthetic rationale"],
                                   missing_information=[]),
                model_version="synthetic-fixture", anonymized_input=request,
            )

    path = tmp_path / "audit.jsonl"
    client = TestClient(create_app(SyntheticProvider(), JsonlAudit(path)))
    response = client.post("/v1/triage", json={
        "language": "en", "patient_context": {"age_group": "adult", "symptoms": ["synthetic"]}
    })
    assert response.status_code == 200
    report = {"records": [{"id": "synthetic-case", "success": True, "response": response.json()}]}
    audit = [json.loads(line) for line in path.read_text().splitlines()]
    assert module.reconcile(report, audit)["matched_audit_entries"] == 1
    audit[0]["output"]["summary"] = "Tampered synthetic response"
    assert module.reconcile(report, audit)["status"] == "failed"
