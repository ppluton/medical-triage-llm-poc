from dataclasses import dataclass
from pathlib import Path

from triage_poc.medquad_audit import (
    audit_medquad,
    audit_presidio_sample,
    build_medquad_review_queue,
    normalize_question,
)


@dataclass
class _Audit:
    detected_entity_counts: dict[str, int]
    residual_entity_counts: dict[str, int]
    status: str


@dataclass
class _Result:
    audit: _Audit
    text: str


class _FakeAnonymizer:
    def anonymize(self, text: str, language: str) -> _Result:
        assert text
        assert language == "en"
        return _Result(_Audit({"PHONE_NUMBER": 1}, {}, "passed"), text)


def _write_xml(path: Path, pairs: list[tuple[str, str]]) -> None:
    pair_xml = "".join(
        f"<QAPair><Question>{question}</Question><Answer>{answer}</Answer></QAPair>"
        for question, answer in pairs
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"<Document><QAPairs>{pair_xml}</QAPairs></Document>", encoding="utf-8")


def test_normalizes_equivalent_question_text():
    assert normalize_question("What is Cancer?") == normalize_question("WHAT IS—CANCER")


def test_audit_counts_content_without_returning_source_text(tmp_path):
    _write_xml(
        tmp_path / "1_CancerGov_QA" / "sample.xml",
        [
            ("What is cancer?", "General answer"),
            ("WHAT IS CANCER", "Contact test@example.org or 202-555-0123"),
        ],
    )
    _write_xml(
        tmp_path / "10_MPlus_ADAM_QA" / "removed.xml",
        [("Removed answer?", "")],
    )

    report = audit_medquad(tmp_path)

    assert report["direct_triage_sft_eligible"] is False
    assert report["totals"]["qa_pairs"] == 3
    assert report["totals"]["nonempty_answers"] == 2
    assert report["totals"]["empty_answers"] == 1
    assert report["totals"]["duplicate_question_instances"] == 1
    assert report["totals"]["email_match_count"] == 1
    assert report["totals"]["phone_match_count"] == 1
    assert "10_MPlus_ADAM_QA" not in report["candidate_knowledge_subsets"]
    assert "General answer" not in str(report)


def test_audit_counts_malformed_xml_without_failing_closed(tmp_path):
    malformed = tmp_path / "1_CancerGov_QA" / "bad.xml"
    malformed.parent.mkdir(parents=True)
    malformed.write_text("<Document>", encoding="utf-8")

    report = audit_medquad(tmp_path)

    assert report["totals"]["malformed_xml_files"] == 1
    assert report["candidate_knowledge_subsets"] == []


def test_presidio_sample_is_deterministic_and_excludes_removed_answers(tmp_path):
    _write_xml(
        tmp_path / "1_CancerGov_QA" / "sample.xml",
        [("Question one?", "Answer one"), ("Question two?", "Answer two")],
    )
    _write_xml(
        tmp_path / "10_MPlus_ADAM_QA" / "removed.xml",
        [("Excluded?", "Unexpected answer")],
    )

    first = audit_presidio_sample(tmp_path, _FakeAnonymizer(), sample_per_subset=1)
    second = audit_presidio_sample(tmp_path, _FakeAnonymizer(), sample_per_subset=1)

    assert first == second
    assert first["sample_count"] == 1
    assert first["sampled_by_subset"] == {"1_CancerGov_QA": 1}
    assert first["detected_entity_counts"] == {"PHONE_NUMBER": 1}
    assert "Question" not in str(first)


def test_review_queue_has_no_automatic_triage_target(tmp_path):
    symptoms_xml = (
        '<Document><QAPairs><QAPair pid="1">'
        '<Question qtype="symptoms">What are the symptoms?</Question>'
        "<Answer>General symptom description.</Answer>"
        "</QAPair></QAPairs></Document>"
    )
    source = tmp_path / "1_CancerGov_QA" / "sample.xml"
    source.parent.mkdir(parents=True)
    source.write_text(symptoms_xml, encoding="utf-8")

    queue = build_medquad_review_queue(tmp_path, _FakeAnonymizer(), limit=10)

    assert queue["status"] == "authoring_queue_not_training_data"
    assert queue["record_count"] == 1
    assert queue["records"][0]["triage_target"] is None
    assert queue["records"][0]["clinical_review_status"] == "not_started"
    assert queue["records"][0]["source_manifest_id"] == "src-medquad-577bd37"


def test_review_queue_round_robins_across_subsets(tmp_path):
    for subset in ("1_CancerGov_QA", "2_GARD_QA"):
        pairs = "".join(
            f'<QAPair pid="{index}"><Question qtype="symptoms">Symptoms {index} '
            f"for {subset}?</Question><Answer>Answer {index}</Answer></QAPair>"
            for index in range(3)
        )
        source = tmp_path / subset / "sample.xml"
        source.parent.mkdir(parents=True)
        source.write_text(f"<Document><QAPairs>{pairs}</QAPairs></Document>", encoding="utf-8")

    queue = build_medquad_review_queue(tmp_path, _FakeAnonymizer(), limit=4)

    subset_counts = {
        subset: sum(record["source_subset"] == subset for record in queue["records"])
        for subset in ("1_CancerGov_QA", "2_GARD_QA")
    }
    assert subset_counts == {"1_CancerGov_QA": 2, "2_GARD_QA": 2}
