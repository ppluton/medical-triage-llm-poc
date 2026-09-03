"""Build a reproducible SFT dataset from source-provided medical QA pairs."""

from __future__ import annotations

import hashlib
from collections import Counter
from collections.abc import Iterable, Mapping
from typing import Protocol

from triage_poc.sft_authoring_queue import (
    MAX_GROUNDING_CHARS,
    SOURCE_METADATA,
    SourceAnchor,
    normalize_for_deduplication,
)

SOURCE_QUOTAS = {
    "medquad": 2_500,
    "mediqal": 1_500,
    "frenchmedmcqa": 1_000,
}
SOURCE_SPLIT_QUOTAS = {
    "medquad": {"train": 2_000, "validation": 250, "test": 250},
    "mediqal": {"train": 1_200, "validation": 150, "test": 150},
    "frenchmedmcqa": {"train": 800, "validation": 100, "test": 100},
}
SOURCE_DIRECT_IDENTIFIER_ENTITIES = (
    "PHONE_NUMBER",
    "EMAIL_ADDRESS",
    "CREDIT_CARD",
    "IBAN_CODE",
    "IP_ADDRESS",
    "PATIENT_REFERENCE",
)
SYSTEM_PROMPT = (
    "You are a medical question-answering assistant used for an educational AI project. "
    "Answer from the provided training example. Do not claim that this answer is a diagnosis, "
    "prescription, or clinically validated triage decision."
)


class AnonymizerLike(Protocol):
    def anonymize(self, text: str, language: str): ...


def _truncate(text: str) -> tuple[str, bool]:
    if len(text) <= MAX_GROUNDING_CHARS:
        return text, False
    return text[:MAX_GROUNDING_CHARS].rstrip(), True


def _record_id(anchor: SourceAnchor) -> str:
    digest = hashlib.sha256(
        f"{anchor.source_name}:{anchor.source_record_id}".encode()
    ).hexdigest()[:24]
    return f"sft-source-{digest}"


def _select_source_records(
    anchors: Iterable[SourceAnchor],
    anonymizer: AnonymizerLike,
    quota: int,
    globally_seen_questions: set[str],
    globally_seen_anonymized_questions: set[str],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    selected: list[dict[str, object]] = []
    counters: Counter[str] = Counter()
    detected_entities: Counter[str] = Counter()

    for anchor in sorted(anchors, key=lambda item: item.selection_digest):
        question_key = normalize_for_deduplication(anchor.question)
        if not question_key or question_key in globally_seen_questions:
            counters["duplicate_questions_skipped"] += 1
            continue

        language = str(SOURCE_METADATA[anchor.source_name]["source_language"])
        question, question_truncated = _truncate(anchor.question)
        answer, answer_truncated = _truncate(anchor.answer)
        question_result = anonymizer.anonymize(question, language)
        answer_result = anonymizer.anonymize(answer, language)
        detected_entities.update(question_result.audit.detected_entity_counts)
        detected_entities.update(answer_result.audit.detected_entity_counts)
        if question_result.audit.status != "passed" or answer_result.audit.status != "passed":
            counters["residual_pii_rejections"] += 1
            continue

        anonymized_question, anonymized_question_truncated = _truncate(question_result.text)
        anonymized_answer, anonymized_answer_truncated = _truncate(answer_result.text)
        if not anonymized_question.strip() or not anonymized_answer.strip():
            counters["empty_after_transformation"] += 1
            continue
        anonymized_question_key = normalize_for_deduplication(anonymized_question)
        if anonymized_question_key in globally_seen_anonymized_questions:
            counters["post_anonymization_duplicates_skipped"] += 1
            continue

        globally_seen_questions.add(question_key)
        globally_seen_anonymized_questions.add(anonymized_question_key)
        selected.append(
            {
                "anchor": anchor,
                "instruction": anonymized_question,
                "response": anonymized_answer,
                "truncated": (
                    question_truncated
                    or answer_truncated
                    or anonymized_question_truncated
                    or anonymized_answer_truncated
                ),
            }
        )
        if len(selected) == quota:
            break

    if len(selected) != quota:
        raise ValueError(
            f"Source quota cannot be met: requested={quota}, selected={len(selected)}."
        )
    return selected, {
        "selected": len(selected),
        **dict(sorted(counters.items())),
        "detected_entity_counts": dict(sorted(detected_entities.items())),
        "truncated_records": sum(bool(item["truncated"]) for item in selected),
    }


def _assign_splits(source_name: str, records: list[dict[str, object]]) -> None:
    offset = 0
    for split in ("train", "validation", "test"):
        count = SOURCE_SPLIT_QUOTAS[source_name][split]
        for record in records[offset : offset + count]:
            record["split"] = split
        offset += count
    if offset != len(records):
        raise ValueError(f"Split quotas do not cover source {source_name}.")


def build_source_sft_dataset(
    source_anchors: Mapping[str, Iterable[SourceAnchor]],
    anonymizer: AnonymizerLike,
    *,
    code_revision: str,
    run_id: str,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Return exactly 5,000 source-derived records with isolated splits."""

    globally_seen_questions: set[str] = set()
    globally_seen_anonymized_questions: set[str] = set()
    records: list[dict[str, object]] = []
    audits: dict[str, object] = {}

    for source_name, quota in SOURCE_QUOTAS.items():
        if source_name not in source_anchors:
            raise ValueError(f"Missing required source iterator: {source_name}.")
        selected, audit = _select_source_records(
            source_anchors[source_name],
            anonymizer,
            quota,
            globally_seen_questions,
            globally_seen_anonymized_questions,
        )
        source_records: list[dict[str, object]] = []
        metadata = SOURCE_METADATA[source_name]
        for item in selected:
            anchor = item["anchor"]
            source_records.append(
                {
                    "schema_version": "1.0.0",
                    "record_id": _record_id(anchor),
                    "task_type": "medical_qa_sft",
                    "language": metadata["source_language"],
                    "instruction": item["instruction"],
                    "response": item["response"],
                    "source": {
                        "source_manifest_id": metadata["manifest_id"],
                        "source_dataset": metadata["dataset"],
                        "source_license": metadata["license"],
                        "source_record_id": anchor.source_record_id,
                        "source_locator": anchor.source_locator,
                    },
                    "transformation": {
                        "pipeline_name": "source_medical_qa_sft",
                        "pipeline_version": "1.0.0",
                        "operations": [
                            "deterministic_selection",
                            "exact_normalized_question_deduplication",
                            "presidio_direct_identifier_anonymization",
                        ],
                        "content_truncated": item["truncated"],
                        "code_revision": code_revision,
                        "run_id": run_id,
                    },
                    "quality": {
                        "pii_anonymization_status": "passed_direct_identifiers_only",
                        "answer_origin": "source_provided",
                        "clinical_review_status": "not_performed",
                    },
                    "split": None,
                    "intended_use": "medical_domain_adaptation_for_triage_poc",
                    "triage_label": None,
                }
            )
        _assign_splits(source_name, source_records)
        records.extend(source_records)
        audits[source_name] = audit

    expected_count = sum(SOURCE_QUOTAS.values())
    if len(records) != expected_count or len({r["record_id"] for r in records}) != expected_count:
        raise ValueError(f"The source SFT dataset must contain {expected_count} unique records.")

    summary = {
        "record_count": len(records),
        "source_counts": dict(
            sorted(Counter(r["source"]["source_dataset"] for r in records).items())
        ),
        "language_counts": dict(sorted(Counter(r["language"] for r in records).items())),
        "split_counts": dict(sorted(Counter(r["split"] for r in records).items())),
        "triage_label_count": sum(r["triage_label"] is not None for r in records),
        "source_audits": audits,
    }
    return records, summary


def render_source_sft_conversation(record: Mapping[str, object]) -> dict[str, object]:
    """Render one canonical record without exposing the test split to training."""

    if record.get("task_type") != "medical_qa_sft":
        raise ValueError("Only medical_qa_sft records can be rendered.")
    if record.get("split") == "test":
        raise ValueError("The test split must remain isolated from training rendering.")
    return {
        "record_id": record["record_id"],
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": record["instruction"]},
            {"role": "assistant", "content": record["response"]},
        ],
    }
