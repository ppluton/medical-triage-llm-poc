from dataclasses import dataclass

import pytest

from triage_poc.sft_authoring_queue import SourceAnchor
from triage_poc.source_sft import build_source_sft_dataset, render_source_sft_conversation


@dataclass
class _Audit:
    detected_entity_counts: dict[str, int]
    status: str


@dataclass
class _Result:
    text: str
    audit: _Audit


class _FakeAnonymizer:
    def anonymize(self, text: str, language: str) -> _Result:
        status = "manual_review_required" if "reject" in text else "passed"
        return _Result(text.replace("Pierre", "<PERSON>"), _Audit({}, status))


def _anchors(source: str, count: int, *, rejected_first: bool = False):
    if rejected_first:
        yield SourceAnchor(source, "reject", "train:reject", "reject", "answer")
    for index in range(count):
        yield SourceAnchor(
            source,
            f"{source}-{index}",
            f"train:{index}",
            f"Unique {source} question {index}",
            f"Source answer {index}",
        )


def _small_quotas(monkeypatch):
    monkeypatch.setattr(
        "triage_poc.source_sft.SOURCE_QUOTAS",
        {"medquad": 2, "mediqal": 2, "frenchmedmcqa": 2},
    )
    monkeypatch.setattr(
        "triage_poc.source_sft.SOURCE_SPLIT_QUOTAS",
        {
            "medquad": {"train": 1, "validation": 1, "test": 0},
            "mediqal": {"train": 1, "validation": 0, "test": 1},
            "frenchmedmcqa": {"train": 1, "validation": 0, "test": 1},
        },
    )


def test_builds_source_provided_records_without_triage_labels(monkeypatch):
    _small_quotas(monkeypatch)
    records, summary = build_source_sft_dataset(
        {source: _anchors(source, 3) for source in ("medquad", "mediqal", "frenchmedmcqa")},
        _FakeAnonymizer(),
        code_revision="abcdef1",
        run_id="test-run",
    )

    assert len(records) == 6
    assert summary["triage_label_count"] == 0
    assert all(record["quality"]["answer_origin"] == "source_provided" for record in records)
    assert all(record["quality"]["clinical_review_status"] == "not_performed" for record in records)
    assert {record["language"] for record in records} == {"fr", "en"}
    assert {record["split"] for record in records} == {"train", "validation", "test"}


def test_rejects_residual_pii_and_replenishes_quota(monkeypatch):
    _small_quotas(monkeypatch)
    records, summary = build_source_sft_dataset(
        {
            source: _anchors(source, 3, rejected_first=True)
            for source in ("medquad", "mediqal", "frenchmedmcqa")
        },
        _FakeAnonymizer(),
        code_revision="abcdef1",
        run_id="test-run",
    )

    assert len(records) == 6
    assert sum(
        audit.get("residual_pii_rejections", 0)
        for audit in summary["source_audits"].values()
    ) > 0


def test_deduplicates_questions_across_sources(monkeypatch):
    _small_quotas(monkeypatch)
    shared = SourceAnchor(
        "mediqal", "shared", "train:shared", "Unique medquad question 0", "answer"
    )
    records, _ = build_source_sft_dataset(
        {
            "medquad": _anchors("medquad", 3),
            "mediqal": [shared, *_anchors("mediqal", 3)],
            "frenchmedmcqa": _anchors("frenchmedmcqa", 3),
        },
        _FakeAnonymizer(),
        code_revision="abcdef1",
        run_id="test-run",
    )
    assert len(records) == 6
    assert len({record["instruction"] for record in records}) == 6


def test_refuses_to_render_test_split(monkeypatch):
    _small_quotas(monkeypatch)
    records, _ = build_source_sft_dataset(
        {source: _anchors(source, 3) for source in ("medquad", "mediqal", "frenchmedmcqa")},
        _FakeAnonymizer(),
        code_revision="abcdef1",
        run_id="test-run",
    )
    test_record = next(record for record in records if record["split"] == "test")
    with pytest.raises(ValueError, match="test split"):
        render_source_sft_conversation(test_record)


def test_production_quotas_match_brief():
    from triage_poc.source_sft import SOURCE_QUOTAS, SOURCE_SPLIT_QUOTAS

    assert sum(SOURCE_QUOTAS.values()) == 5_000
    assert sum(quotas["train"] for quotas in SOURCE_SPLIT_QUOTAS.values()) == 4_000
    assert sum(quotas["validation"] for quotas in SOURCE_SPLIT_QUOTAS.values()) == 500
    assert sum(quotas["test"] for quotas in SOURCE_SPLIT_QUOTAS.values()) == 500
