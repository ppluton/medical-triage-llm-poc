from dataclasses import dataclass

import pytest
from presidio_analyzer import RecognizerResult

from triage_poc.anonymization import AnonymizationConfigurationError, TextAnonymizer
from triage_poc.contracts import ContractValidationError, validate_against_schema


@dataclass
class FakeOutput:
    text: str


class FakeAnalyzer:
    def __init__(self, responses):
        self.responses = iter(responses)

    def analyze(self, *, text, entities, language):
        return next(self.responses)


class FakeAnonymizer:
    def anonymize(self, *, text, analyzer_results, operators):
        output = text
        for result in sorted(analyzer_results, key=lambda item: item.start, reverse=True):
            output = output[: result.start] + f"<{result.entity_type}>" + output[result.end :]
        return FakeOutput(output)


def test_anonymize_replaces_detected_pii_and_keeps_a_pii_free_audit():
    source = "Patient id: AB-1234 ; email: jeanne.dupont@example.test"
    detections = [
        RecognizerResult(entity_type="PATIENT_REFERENCE", start=0, end=19, score=0.9),
        RecognizerResult(entity_type="EMAIL_ADDRESS", start=29, end=len(source), score=0.9),
    ]
    result = TextAnonymizer(
        FakeAnalyzer([detections, []]), FakeAnonymizer()
    ).anonymize(source, "fr")

    assert result.text == "<PATIENT_REFERENCE> ; email: <EMAIL_ADDRESS>"
    assert result.audit.detected_entity_counts == {"EMAIL_ADDRESS": 1, "PATIENT_REFERENCE": 1}
    assert result.audit.residual_entity_counts == {}
    assert result.audit.status == "passed"
    assert source not in repr(result.audit)
    assert "jeanne.dupont@example.test" not in repr(result.audit)


def test_anonymize_marks_manual_review_when_pii_is_still_detected():
    detection = RecognizerResult(entity_type="PHONE_NUMBER", start=0, end=5, score=0.9)
    result = TextAnonymizer(FakeAnalyzer([[detection], [detection]]), FakeAnonymizer()).anonymize(
        "06 12", "fr"
    )

    assert result.audit.status == "manual_review_required"
    assert result.audit.residual_entity_counts == {"PHONE_NUMBER": 1}


def test_anonymize_rejects_unsupported_language_before_processing():
    with pytest.raises(AnonymizationConfigurationError, match="Unsupported language"):
        TextAnonymizer(FakeAnalyzer([]), FakeAnonymizer()).anonymize("synthetic text", "de")


def test_anonymize_rejects_empty_text_before_processing():
    with pytest.raises(ValueError, match="must not be empty"):
        TextAnonymizer(FakeAnalyzer([]), FakeAnonymizer()).anonymize("  ", "fr")


def test_anonymize_fails_closed_when_detector_raises():
    class BrokenAnalyzer:
        def analyze(self, *, text, entities, language):
            raise RuntimeError("model unavailable")

    with pytest.raises(AnonymizationConfigurationError, match="could not complete safely"):
        TextAnonymizer(BrokenAnalyzer(), FakeAnonymizer()).anonymize("synthetic text", "fr")


def test_contract_rejects_an_approved_manifest_with_a_skipped_pii_check():
    manifest = {
        "schema_version": "1.0.0",
        "manifest_id": "src-fixture-source",
        "dataset_name": "fixture",
        "primary_url": "https://example.org/dataset",
        "immutable_revision": "abcdef1",
        "artifact": {
            "upstream_path": "fixture.jsonl",
            "retrieved_at": "2026-08-28T00:00:00Z",
            "byte_size": 1,
            "sha256": "a" * 64,
            "local_storage_uri": "file:///controlled/fixture.jsonl",
        },
        "license": {
            "identifier": "MIT",
            "url": "https://opensource.org/license/mit",
            "attribution_required": True,
            "restrictions": [],
        },
        "citation": "Synthetic fixture",
        "admission_status": "approved",
        "pre_ingestion_checks": {
            "provenance": "passed",
            "license": "passed",
            "pii": "not_run",
            "format": "passed",
            "duplicates": "passed",
            "split_leakage": "passed",
        },
    }

    with pytest.raises(ContractValidationError, match="passed"):
        validate_against_schema(manifest, "source_manifest_v1.schema.json")
