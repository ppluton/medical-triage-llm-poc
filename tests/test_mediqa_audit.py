from dataclasses import dataclass
from pathlib import Path

from triage_poc.mediqa_audit import audit_mediqa, audit_presidio_question_sample, normalize_text


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
        return _Result(_Audit({"PERSON": 1}, {}, "passed"), text)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_normalizes_equivalent_text():
    assert normalize_text("Chest pain?") == normalize_text("CHEST—PAIN")


def test_audit_prefers_labeled_test_export_and_returns_no_source_text(tmp_path):
    task2 = tmp_path / "MEDIQA_Task2_RQE"
    unlabeled = (
        "<Root><pair pid='1'><chq>Call [NAME] at 202-555-0123</chq>"
        "<faq>Chest pain?</faq></pair></Root>"
    )
    labeled = (
        "<Root><pair pid='1' value='true'><chq>Call [NAME] at 202-555-0123</chq>"
        "<faq>Chest pain?</faq></pair></Root>"
    )
    _write(task2 / "MEDIQA2019-Task2-RQE-TestSet.xml", unlabeled)
    _write(task2 / "MEDIQA2019-Task2-RQE-TestSet-wLabels.xml", labeled)

    report = audit_mediqa(tmp_path)

    assert report["direct_triage_sft_eligible"] is False
    assert report["task1_mednli_included"] is False
    assert report["totals"]["records"] == 1
    assert report["totals"]["positive_labels"] == 1
    assert report["totals"]["placeholder_count"] == 1
    assert report["totals"]["phone_match_count"] == 1
    assert "Chest pain" not in str(report)


def test_audit_counts_qa_scores_and_duplicates(tmp_path):
    qa_xml = """<Root>
    <Question QID='1'><QuestionText>What is flu?</QuestionText><AnswerList>
      <Answer ReferenceScore='4'><AnswerText>Answer one</AnswerText></Answer>
    </AnswerList></Question>
    <Question QID='2'><QuestionText>WHAT IS FLU</QuestionText><AnswerList>
      <Answer ReferenceScore='1'><AnswerText>Answer two</AnswerText></Answer>
    </AnswerList></Question></Root>"""
    _write(tmp_path / "MEDIQA_Task3_QA" / "MEDIQA2019-Task3-QA-ValidationSet.xml", qa_xml)

    report = audit_mediqa(tmp_path)

    assert report["totals"]["records"] == 2
    assert report["totals"]["answers"] == 2
    assert report["totals"]["answer_score_1"] == 1
    assert report["totals"]["answer_score_4"] == 1
    assert report["duplicate_instances"]["qa_question"] == 1


def test_presidio_question_sample_is_deterministic_and_skips_unlabeled_duplicate(tmp_path):
    task2 = tmp_path / "MEDIQA_Task2_RQE"
    pair = "<Root><pair pid='1' value='false'><chq>Question</chq><faq>FAQ</faq></pair></Root>"
    _write(task2 / "MEDIQA2019-Task2-RQE-TestSet.xml", pair)
    _write(task2 / "MEDIQA2019-Task2-RQE-TestSet-wLabels.xml", pair)

    first = audit_presidio_question_sample(tmp_path, _FakeAnonymizer(), sample_per_file=1)
    second = audit_presidio_question_sample(tmp_path, _FakeAnonymizer(), sample_per_file=1)

    assert first == second
    assert first["sample_count"] == 1
    assert first["detected_entity_counts"] == {"PERSON": 1}
    assert "Question" not in str(first)
