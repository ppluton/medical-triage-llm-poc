import json
import stat

import pytest
from presidio_analyzer import RecognizerResult

from triage_poc.privacy_audit import audit_contextual_pii, prepare_direct_identifier_review


class FakeAnalyzer:
    def analyze(self, *, text, entities, language):
        matches = []
        for token, entity in (
            ("Alice", "PERSON"),
            ("Patient Bob", "PATIENT_NAME"),
            ("alice@example.com", "EMAIL_ADDRESS"),
        ):
            if token in text:
                start = text.index(token)
                matches.append(RecognizerResult(entity, start, start + len(token), 0.9))
        return matches


def _row(record_id, split, instruction, response):
    return {
        "record_id": record_id,
        "split": split,
        "language": "en",
        "instruction": instruction,
        "response": response,
        "source": {"source_manifest_id": "source-fixture"},
    }


def test_contextual_audit_keeps_text_out_of_decisions_and_summary(tmp_path):
    canonical = tmp_path / "canonical.jsonl"
    rows = [
        _row("clear", "train", "Medical question", "Medical answer"),
        _row("context", "validation", "What did Alice report?", "No contact details"),
        _row("direct", "test", "Patient Bob", "alice@example.com"),
    ]
    canonical.write_text("".join(json.dumps(row) + "\n" for row in rows))
    output = tmp_path / "audit"
    summary = audit_contextual_pii(canonical, output, analyzer=FakeAnalyzer())

    decisions = [json.loads(line) for line in (output / "decisions.jsonl").read_text().splitlines()]
    assert [row["status"] for row in decisions] == [
        "passed_no_contextual_detection",
        "contextual_review_required",
        "manual_review_required_direct_identifier",
    ]
    assert "Alice" not in (output / "decisions.jsonl").read_text()
    assert "alice@example.com" not in json.dumps(summary)
    assert summary["fields_scanned"] == 6
    assert summary["input"]["records"] == 3
    assert summary["split_counts"] == {"test": 1, "train": 1, "validation": 1}
    assert "Alice" in (output / "findings-private.jsonl").read_text()
    assert stat.S_IMODE(output.stat().st_mode) == 0o700
    assert stat.S_IMODE((output / "findings-private.jsonl").stat().st_mode) == 0o600
    assert stat.S_IMODE((output / "decisions.jsonl").stat().st_mode) == 0o600
    assert stat.S_IMODE((output / "summary.json").stat().st_mode) == 0o600


def test_contextual_audit_requires_fresh_output(tmp_path):
    canonical = tmp_path / "canonical.jsonl"
    canonical.write_text(json.dumps(_row("one", "train", "Question", "Answer")) + "\n")
    output = tmp_path / "existing"
    output.mkdir()
    with pytest.raises(ValueError, match="fresh"):
        audit_contextual_pii(canonical, output, analyzer=FakeAnalyzer())


def test_direct_review_queue_excludes_contextual_entities_and_stays_private(tmp_path):
    findings = tmp_path / "findings-private.jsonl"
    rows = [
        {
            "record_id": "context",
            "split": "train",
            "source_manifest_id": "source-fixture",
            "field": "instruction",
            "entity": "PERSON",
            "score": 0.9,
            "span": "Alice",
            "context": "What did Alice report?",
        },
        {
            "record_id": "direct",
            "split": "validation",
            "source_manifest_id": "source-fixture",
            "field": "response",
            "entity": "PATIENT_NAME",
            "score": 0.9,
            "span": "Patient Bob",
            "context": "Patient Bob reported a synthetic symptom.",
        },
    ]
    findings.write_text("".join(json.dumps(row) + "\n" for row in rows))
    output = tmp_path / "private" / "direct-review-private.jsonl"

    summary = prepare_direct_identifier_review(findings, output)

    queue = [json.loads(line) for line in output.read_text().splitlines()]
    assert summary["findings"] == 1
    assert summary["records"] == 1
    assert summary["entity_counts"] == {"PATIENT_NAME": 1}
    assert queue[0]["record_id"] == "direct"
    assert queue[0]["review"]["classification"] is None
    assert "Alice" not in output.read_text()
    assert stat.S_IMODE(output.parent.stat().st_mode) == 0o700
    assert stat.S_IMODE(output.stat().st_mode) == 0o600
