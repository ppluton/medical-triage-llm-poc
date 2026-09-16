import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from triage_poc.privacy_finalize import finalize_sft_privacy, sha256
from triage_poc.source_sft_preflight import validate_source_sft_artifacts


def _write_jsonl(path, rows):
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))


def _row(record_id, split, instruction, response):
    return {
        "schema_version": "2.0.0",
        "record_id": record_id,
        "task_type": "medical_qa_sft",
        "language": "en",
        "instruction": instruction,
        "response": response,
        "source": {
            "source_manifest_id": "src-medquad-577bd37",
            "source_dataset": "abachaa/MedQuAD",
            "source_license": "CC-BY-4.0",
            "source_record_id": record_id,
            "source_locator": record_id,
        },
        "transformation": {
            "pipeline_name": "source_medical_qa_sft",
            "pipeline_version": "2.0.0",
            "operations": ["deterministic_selection"],
            "content_truncated": False,
            "code_revision": "old",
            "run_id": "old",
        },
        "quality": {
            "pii_anonymization_status": "passed_direct_identifiers_only",
            "answer_origin": "source_provided",
            "clinical_review_status": "not_performed",
        },
        "split": split,
        "intended_use": "medical_domain_adaptation_for_triage_poc",
        "triage_label": None,
    }


def _finding(row, field, entity, span):
    text = row[field]
    start = text.index(span)
    return {
        "record_id": row["record_id"],
        "split": row["split"],
        "source_manifest_id": row["source"]["source_manifest_id"],
        "field": field,
        "entity": entity,
        "score": 0.85,
        "start": start,
        "end": start + len(span),
        "span": span,
        "context": text,
    }


def test_finalizes_direct_masks_and_keeps_test_isolated(tmp_path):
    rows = [
        _row(
            "sft-source-000000000000000000000001",
            "train",
            "Patient name is Alice Smith",
            "Medical answer",
        ),
        _row(
            "sft-source-000000000000000000000002",
            "validation",
            "Question about Paris",
            "Medical answer",
        ),
        _row(
            "sft-source-000000000000000000000003",
            "test",
            "Reserved question",
            "Reserved answer",
        ),
    ]
    canonical = tmp_path / "canonical.jsonl"
    findings = tmp_path / "findings.jsonl"
    _write_jsonl(canonical, rows)
    _write_jsonl(
        findings,
        [
            _finding(rows[0], "instruction", "PATIENT_NAME", "Patient name is Alice Smith"),
            _finding(rows[1], "instruction", "LOCATION", "Paris"),
        ],
    )
    output = tmp_path / "output"
    manifest = finalize_sft_privacy(
        canonical,
        findings,
        output,
        expected_canonical_sha256=sha256(canonical),
        expected_findings_sha256=sha256(findings),
        code_revision="abc1234",
        run_id="privacy-fixture",
    )
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest))

    _, finalized, train, validation = validate_source_sft_artifacts(manifest_path, output)
    schema = json.loads(
        (
            Path(__file__).parents[1]
            / "data/manifests/source_medical_qa_sft_v2_2.schema.json"
        ).read_text()
    )
    validator = Draft202012Validator(schema)
    for row in finalized:
        validator.validate(row)
    assert len(finalized) == 3
    assert len(train) == len(validation) == 1
    assert finalized[0]["instruction"] == "<PATIENT_NAME>"
    assert finalized[0]["quality"]["pii_anonymization_status"] == (
        "passed_technical_privacy_controls"
    )
    assert finalized[1]["instruction"] == "Question about Paris"
    assert manifest["privacy_review"]["direct_findings_masked"] == 1
    assert manifest["privacy_review"]["contextual_records_disposed"] == 1
    assert manifest["privacy_review"]["external_publication_status"].startswith("blocked")
    assert not any(
        row["record_id"] == "sft-source-000000000000000000000003"
        for row in train + validation
    )


def test_fails_closed_on_checksum_or_span_drift(tmp_path):
    row = _row(
        "sft-source-000000000000000000000001",
        "train",
        "Patient name is Alice",
        "Answer",
    )
    canonical = tmp_path / "canonical.jsonl"
    findings = tmp_path / "findings.jsonl"
    _write_jsonl(canonical, [row])
    finding = _finding(row, "instruction", "PATIENT_NAME", "Patient name is Alice")
    _write_jsonl(findings, [finding])

    with pytest.raises(ValueError, match="Canonical checksum"):
        finalize_sft_privacy(
            canonical,
            findings,
            tmp_path / "bad-checksum",
            expected_canonical_sha256="0" * 64,
            expected_findings_sha256=sha256(findings),
            code_revision="abc1234",
            run_id="privacy-fixture",
        )

    finding["span"] = "different"
    _write_jsonl(findings, [finding])
    with pytest.raises(ValueError, match="does not match"):
        finalize_sft_privacy(
            canonical,
            findings,
            tmp_path / "span-drift",
            expected_canonical_sha256=sha256(canonical),
            expected_findings_sha256=sha256(findings),
            code_revision="abc1234",
            run_id="privacy-fixture",
        )
