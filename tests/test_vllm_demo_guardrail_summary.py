import json

from scripts.run_vllm_api_demo import summarize_guardrail_audit


def _response(identifier, success=True):
    return {
        "id": identifier,
        "success": success,
        "response": {"interaction_id": f"interaction-{identifier}"},
    }


def test_guardrail_audit_summary_is_text_free_and_versioned(tmp_path):
    report = tmp_path / "endpoint.json"
    audit = tmp_path / "audit.jsonl"
    report.write_text(json.dumps({"records": [_response("one"), _response("two")]}))
    audit.write_text(
        "\n".join(
            json.dumps(row)
            for row in (
                {
                    "interaction_id": "interaction-one",
                    "guardrail_status": "model_output",
                    "guardrail_version": "proposed-guardrails-v1",
                    "guardrail_reasons": [],
                    "anonymized_input": {"symptoms": ["private synthetic text"]},
                },
                {
                    "interaction_id": "interaction-two",
                    "guardrail_status": "safe_fallback",
                    "guardrail_version": "proposed-guardrails-v1",
                    "guardrail_reasons": ["invented_stability_or_absence"],
                    "anonymized_input": {"symptoms": ["other private synthetic text"]},
                },
            )
        )
        + "\n"
    )

    summary = summarize_guardrail_audit(report, audit)

    assert summary["status"] == "passed"
    assert summary["guardrail_status_counts"] == {"model_output": 1, "safe_fallback": 1}
    assert summary["guardrail_reason_counts"] == {"invented_stability_or_absence": 1}
    assert "private synthetic text" not in json.dumps(summary)


def test_guardrail_audit_summary_rejects_missing_or_unversioned_entries(tmp_path):
    report = tmp_path / "endpoint.json"
    audit = tmp_path / "audit.jsonl"
    report.write_text(json.dumps({"records": [_response("one"), _response("missing")]}))
    audit.write_text(
        json.dumps(
            {
                "interaction_id": "interaction-one",
                "guardrail_status": "corrected",
                "guardrail_version": "old-version",
                "guardrail_reasons": ["priority_floor"],
            }
        )
        + "\n"
    )

    summary = summarize_guardrail_audit(report, audit)

    assert summary["status"] == "failed"
    assert summary["issue_counts"] == {
        "missing_or_duplicate_audit_entry": 1,
        "unexpected_guardrail_version": 1,
    }
