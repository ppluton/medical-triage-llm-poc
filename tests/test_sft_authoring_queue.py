from dataclasses import dataclass

import pytest

from triage_poc.sft_authoring_queue import (
    RISK_FAMILY_CANDIDATE_QUOTAS,
    SOURCE_ANCHOR_QUOTAS,
    SourceAnchor,
    build_sft_authoring_queue,
)


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
        assert language in {"fr", "en"}
        status = "manual_review_required" if "reject-me" in text else "passed"
        return _Result(text.replace("Pierre", "<PERSON>"), _Audit({"PERSON": 1}, status))


def _anchors(source_name: str, count: int, *, rejected_first: bool = False):
    if rejected_first:
        yield SourceAnchor(source_name, "rejected", "rejected", "reject-me", "answer")
    for index in range(count):
        yield SourceAnchor(
            source_name=source_name,
            source_record_id=f"record-{index}",
            source_locator=f"source:{index}",
            question=f"Unique question {index} for {source_name}",
            answer=f"Grounding answer {index} for {source_name}",
        )


def test_builds_exact_bilingual_non_trainable_queue(monkeypatch):
    monkeypatch.setattr(
        "triage_poc.sft_authoring_queue.SOURCE_ANCHOR_QUOTAS",
        {"medquad": 2, "mediqa2019": 1, "frenchmedmcqa": 1},
    )
    monkeypatch.setattr(
        "triage_poc.sft_authoring_queue.RISK_FAMILY_CANDIDATE_QUOTAS",
        {"chest_pain": 4, "other": 4},
    )
    queue = build_sft_authoring_queue(
        {
            "medquad": _anchors("medquad", 2),
            "mediqa2019": _anchors("mediqa2019", 1),
            "frenchmedmcqa": _anchors("frenchmedmcqa", 1),
        },
        _FakeAnonymizer(),
        code_revision="abcdef1",
        run_id="unit-test",
    )

    records = queue["records"]
    assert len(records) == 8
    assert {record["requested_language"] for record in records} == {"fr", "en"}
    assert all(record["training_eligible"] is False for record in records)
    assert all(record["draft"]["triage_level"] is None for record in records)
    assert all(record["split"] is None for record in records)
    assert all(record["quality"]["clinical_review_status"] == "not_started" for record in records)
    assert len({record["bilingual_group_id"] for record in records}) == 4


def test_fails_closed_when_source_quota_cannot_be_met(monkeypatch):
    monkeypatch.setattr(
        "triage_poc.sft_authoring_queue.SOURCE_ANCHOR_QUOTAS",
        {"medquad": 2, "mediqa2019": 1, "frenchmedmcqa": 1},
    )
    monkeypatch.setattr(
        "triage_poc.sft_authoring_queue.RISK_FAMILY_CANDIDATE_QUOTAS",
        {"other": 8},
    )
    with pytest.raises(ValueError, match="Source quota cannot be met"):
        build_sft_authoring_queue(
            {
                "medquad": _anchors("medquad", 1),
                "mediqa2019": _anchors("mediqa2019", 1),
                "frenchmedmcqa": _anchors("frenchmedmcqa", 1),
            },
            _FakeAnonymizer(),
            code_revision="abcdef1",
            run_id="unit-test",
        )


def test_rejects_residual_pii_and_replenishes_quota(monkeypatch):
    monkeypatch.setattr(
        "triage_poc.sft_authoring_queue.SOURCE_ANCHOR_QUOTAS",
        {"medquad": 1, "mediqa2019": 1, "frenchmedmcqa": 1},
    )
    monkeypatch.setattr(
        "triage_poc.sft_authoring_queue.RISK_FAMILY_CANDIDATE_QUOTAS",
        {"other": 6},
    )
    queue = build_sft_authoring_queue(
        {
            source: _anchors(source, 2, rejected_first=True)
            for source in SOURCE_ANCHOR_QUOTAS
        },
        _FakeAnonymizer(),
        code_revision="abcdef1",
        run_id="unit-test",
    )

    assert sum(
        audit["rejected_residual_pii"] for audit in queue["source_audits"].values()
    ) > 0
    assert len(queue["records"]) == 6


def test_production_quotas_describe_five_thousand_candidates():
    assert sum(SOURCE_ANCHOR_QUOTAS.values()) * 2 == 5_000
    assert sum(RISK_FAMILY_CANDIDATE_QUOTAS.values()) == 5_000
    assert all(quota % 2 == 0 for quota in RISK_FAMILY_CANDIDATE_QUOTAS.values())
