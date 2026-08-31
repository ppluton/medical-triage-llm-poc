"""Build a governed, non-trainable authoring queue for future triage SFT records."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from triage_poc.medquad_audit import REMOVED_ANSWER_SUBSETS

LANGUAGES = ("fr", "en")
SOURCE_ANCHOR_QUOTAS = {
    "medquad": 1_000,
    "mediqa2019": 750,
    "frenchmedmcqa": 750,
}
RISK_FAMILY_CANDIDATE_QUOTAS = {
    "chest_pain": 600,
    "respiratory_distress": 600,
    "neurological_deficit": 600,
    "pediatric": 560,
    "pregnancy": 560,
    "vulnerability": 560,
    "insufficient_information": 560,
    "contradictory_information": 480,
    "other": 480,
}
SOURCE_METADATA = {
    "medquad": {
        "manifest_id": "src-medquad-577bd37",
        "dataset": "abachaa/MedQuAD",
        "license": "CC-BY-4.0",
        "source_language": "en",
    },
    "mediqa2019": {
        "manifest_id": "src-mediqa2019-32311a1",
        "dataset": "abachaa/MEDIQA2019",
        "license": "CC-BY-4.0",
        "source_language": "en",
    },
    "frenchmedmcqa": {
        "manifest_id": "src-frenchmedmcqa-deft-2023-full",
        "dataset": "qanastek/frenchmedmcqa",
        "license": "Apache-2.0",
        "source_language": "fr",
    },
}
MAX_GROUNDING_CHARS = 4_000


class AnonymizerLike(Protocol):
    def anonymize(self, text: str, language: str): ...


@dataclass(frozen=True)
class SourceAnchor:
    source_name: str
    source_record_id: str
    source_locator: str
    question: str
    answer: str

    @property
    def selection_digest(self) -> str:
        return hashlib.sha256(
            f"{self.source_name}:{self.source_record_id}".encode()
        ).hexdigest()


def normalize_for_deduplication(text: str) -> str:
    """Normalize exact lexical content without claiming semantic deduplication."""

    normalized = unicodedata.normalize("NFKC", text).casefold()
    return re.sub(r"\W+", "", normalized)


def _stable_source_id(locator: str) -> str:
    return hashlib.sha256(locator.encode()).hexdigest()


def iter_medquad_anchors(repository_path: Path) -> Iterator[SourceAnchor]:
    """Yield non-empty MedQuAD QA anchors outside copyright-removed subsets."""

    for subset_path in sorted(repository_path.iterdir()):
        if (
            not subset_path.is_dir()
            or subset_path.name in REMOVED_ANSWER_SUBSETS
            or not subset_path.name[0].isdigit()
        ):
            continue
        for xml_path in sorted(subset_path.rglob("*.xml")):
            try:
                root = ET.parse(xml_path).getroot()
            except ET.ParseError:
                continue
            relative_path = xml_path.relative_to(repository_path).as_posix()
            for row_number, pair in enumerate(root.findall(".//QAPair"), start=1):
                question = (pair.findtext("Question") or "").strip()
                answer = (pair.findtext("Answer") or "").strip()
                if not question or not answer:
                    continue
                locator = f"{relative_path}:{pair.get('pid') or row_number}"
                yield SourceAnchor(
                    source_name="medquad",
                    source_record_id=_stable_source_id(locator),
                    source_locator=locator,
                    question=question,
                    answer=answer,
                )


def _mediqa_file_description(xml_path: Path) -> tuple[str, str, bool]:
    name = xml_path.name.lower()
    task = "rqe" if "task2-rqe" in name else "qa"
    split = "train" if "training" in name else "validation" if "validation" in name else "test"
    labeled_peer = xml_path.with_name(xml_path.stem + "-wLabels.xml")
    canonical = not (split == "test" and "-wlabels" not in name and labeled_peer.exists())
    return task, split, canonical


def iter_mediqa_anchors(repository_path: Path) -> Iterator[SourceAnchor]:
    """Yield relevant train/validation QA and positive-RQE knowledge anchors."""

    for xml_path in sorted(repository_path.rglob("*.xml")):
        task, split, canonical = _mediqa_file_description(xml_path)
        if not canonical or split == "test":
            continue
        try:
            root = ET.parse(xml_path).getroot()
        except ET.ParseError:
            continue
        relative_path = xml_path.relative_to(repository_path).as_posix()
        if task == "rqe":
            for row_number, pair in enumerate(root.findall(".//pair"), start=1):
                if pair.get("value") != "true":
                    continue
                question = (pair.findtext("chq") or "").strip()
                answer = (pair.findtext("faq") or "").strip()
                if not question or not answer:
                    continue
                locator = f"{relative_path}:{pair.get('pid') or row_number}"
                yield SourceAnchor(
                    source_name="mediqa2019",
                    source_record_id=_stable_source_id(locator),
                    source_locator=locator,
                    question=question,
                    answer=answer,
                )
        else:
            for row_number, question_node in enumerate(root.findall(".//Question"), start=1):
                question = (question_node.findtext("QuestionText") or "").strip()
                answers = [
                    (answer.findtext("AnswerText") or "").strip()
                    for answer in question_node.findall(".//Answer")
                    if answer.get("ReferenceScore") in {"3", "4"}
                ]
                answer = "\n".join(value for value in answers if value)
                if not question or not answer:
                    continue
                locator = f"{relative_path}:{question_node.get('QID') or row_number}"
                yield SourceAnchor(
                    source_name="mediqa2019",
                    source_record_id=_stable_source_id(locator),
                    source_locator=locator,
                    question=question,
                    answer=answer,
                )


def iter_frenchmedmcqa_anchors(processed_path: Path) -> Iterator[SourceAnchor]:
    """Yield reconstructed train/validation MCQA anchors, never test rows."""

    for split in ("train", "validation"):
        source_path = processed_path / f"{split}.json"
        rows = json.loads(source_path.read_text(encoding="utf-8"))
        for row in rows:
            question = str(row.get("question", "")).strip()
            answers = row.get("answers", {})
            correct_keys = row.get("correct_answers", [])
            correct_answers = [str(answers[key]).strip() for key in correct_keys if key in answers]
            answer = "\n".join(value for value in correct_answers if value)
            if not question or not answer:
                continue
            source_record_id = str(row.get("id", "")).strip()
            locator = f"{split}:{source_record_id}"
            yield SourceAnchor(
                source_name="frenchmedmcqa",
                source_record_id=source_record_id or _stable_source_id(locator),
                source_locator=locator,
                question=question,
                answer=answer,
            )


def _truncate(text: str) -> tuple[str, bool]:
    if len(text) <= MAX_GROUNDING_CHARS:
        return text, False
    return text[:MAX_GROUNDING_CHARS].rstrip(), True


def _select_anonymized_anchors(
    anchors: Iterable[SourceAnchor],
    anonymizer: AnonymizerLike,
    quota: int,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    selected: list[dict[str, object]] = []
    rejected_residual_pii = 0
    duplicate_anchors = 0
    detected_entities: Counter[str] = Counter()
    seen_questions: set[str] = set()

    for anchor in sorted(anchors, key=lambda item: item.selection_digest):
        question_key = normalize_for_deduplication(anchor.question)
        if not question_key or question_key in seen_questions:
            duplicate_anchors += 1
            continue
        question, question_truncated = _truncate(anchor.question)
        answer, answer_truncated = _truncate(anchor.answer)
        language = str(SOURCE_METADATA[anchor.source_name]["source_language"])
        question_result = anonymizer.anonymize(question, language)
        answer_result = anonymizer.anonymize(answer, language)
        detected_entities.update(question_result.audit.detected_entity_counts)
        detected_entities.update(answer_result.audit.detected_entity_counts)
        if question_result.audit.status != "passed" or answer_result.audit.status != "passed":
            rejected_residual_pii += 1
            continue
        anonymized_question, anonymized_question_truncated = _truncate(question_result.text)
        anonymized_answer, anonymized_answer_truncated = _truncate(answer_result.text)
        seen_questions.add(question_key)
        selected.append(
            {
                "anchor": anchor,
                "question": anonymized_question,
                "answer": anonymized_answer,
                "grounding_truncated": question_truncated
                or answer_truncated
                or anonymized_question_truncated
                or anonymized_answer_truncated,
            }
        )
        if len(selected) == quota:
            break

    if len(selected) != quota:
        raise ValueError(
            f"Source quota cannot be met: requested={quota}, selected={len(selected)}."
        )
    return selected, {
        "selected_anchors": len(selected),
        "rejected_residual_pii": rejected_residual_pii,
        "duplicate_anchors_skipped": duplicate_anchors,
        "detected_entity_counts": dict(sorted(detected_entities.items())),
        "truncated_anchors": sum(bool(item["grounding_truncated"]) for item in selected),
    }


def _risk_family_assignments() -> list[str]:
    assignments: list[str] = []
    for family, candidate_quota in RISK_FAMILY_CANDIDATE_QUOTAS.items():
        if candidate_quota % len(LANGUAGES):
            raise ValueError(f"Risk-family quota must support bilingual pairs: {family}.")
        assignments.extend([family] * (candidate_quota // len(LANGUAGES)))
    return assignments


def build_sft_authoring_queue(
    source_anchors: Mapping[str, Iterable[SourceAnchor]],
    anonymizer: AnonymizerLike,
    *,
    code_revision: str,
    run_id: str,
) -> dict[str, object]:
    """Return exactly 5,000 source-grounded tasks that cannot yet enter training."""

    selected_by_source: dict[str, list[dict[str, object]]] = {}
    source_audits: dict[str, object] = {}
    for source_name, quota in SOURCE_ANCHOR_QUOTAS.items():
        if source_name not in source_anchors:
            raise ValueError(f"Missing required source iterator: {source_name}.")
        selected, audit = _select_anonymized_anchors(
            source_anchors[source_name], anonymizer, quota
        )
        selected_by_source[source_name] = selected
        source_audits[source_name] = audit

    selected = [item for values in selected_by_source.values() for item in values]
    selected.sort(key=lambda item: item["anchor"].selection_digest)
    risk_families = _risk_family_assignments()
    if len(selected) != len(risk_families):
        raise ValueError("Source and risk-family quotas do not produce the same anchor count.")

    records: list[dict[str, object]] = []
    for selected_anchor, risk_family in zip(selected, risk_families, strict=True):
        anchor = selected_anchor["anchor"]
        metadata = SOURCE_METADATA[anchor.source_name]
        bilingual_group_id = f"sft-authoring-group-{anchor.selection_digest[:20]}"
        for language in LANGUAGES:
            candidate_id = f"sft-candidate-{anchor.selection_digest[:20]}-{language}"
            records.append(
                {
                    "schema_version": "1.0.0",
                    "candidate_id": candidate_id,
                    "bilingual_group_id": bilingual_group_id,
                    "requested_language": language,
                    "requested_risk_family": risk_family,
                    "risk_family_status": "proposed_authoring_quota_only",
                    "source": {
                        "source_manifest_id": metadata["manifest_id"],
                        "source_dataset": metadata["dataset"],
                        "source_license": metadata["license"],
                        "source_record_id": anchor.source_record_id,
                        "source_locator": anchor.source_locator,
                        "source_language": metadata["source_language"],
                    },
                    "grounding": {
                        "question": selected_anchor["question"],
                        "answer": selected_anchor["answer"],
                        "truncated": selected_anchor["grounding_truncated"],
                    },
                    "draft": {
                        "patient_context": None,
                        "instruction": None,
                        "response": None,
                        "triage_level": None,
                    },
                    "quality": {
                        "pii_anonymization_status": "passed",
                        "source_relevance_review_status": "not_started",
                        "clinical_review_status": "not_started",
                        "safety_review_status": "not_started",
                    },
                    "transformation": {
                        "pipeline_name": "sft_authoring_queue",
                        "pipeline_version": "1.0.0",
                        "code_revision": code_revision,
                        "run_id": run_id,
                    },
                    "split": None,
                    "training_eligible": False,
                }
            )

    return {
        "status": "authoring_queue_not_training_data",
        "records": records,
        "source_audits": source_audits,
        "limits": [
            "Source labels and requested risk families are not triage labels.",
            "Every scenario and target must be written and clinically approved independently.",
            "Exact normalized deduplication does not detect semantic paraphrases.",
            "A passed Presidio scan does not replace human privacy review.",
        ],
    }
