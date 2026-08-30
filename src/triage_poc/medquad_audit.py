"""Privacy-minimizing inventory helpers for the candidate MedQuAD source."""

from __future__ import annotations

import hashlib
import re
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol

REMOVED_ANSWER_SUBSETS = {
    "10_MPlus_ADAM_QA",
    "11_MPlusDrugs_QA",
    "12_MPlusHerbsSupplements_QA",
}
EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_PATTERN = re.compile(r"(?<!\d)(?:\+?1[ .-]?)?(?:\(?\d{3}\)?[ .-]?)\d{3}[ .-]\d{4}(?!\d)")


@dataclass(frozen=True)
class MedquadSubsetAudit:
    subset: str
    xml_files: int
    qa_pairs: int
    nonempty_answers: int
    empty_answers: int
    duplicate_question_instances: int
    email_match_count: int
    phone_match_count: int
    malformed_xml_files: int
    answers_removed_upstream: bool


class AnonymizerLike(Protocol):
    def anonymize(self, text: str, language: str): ...


def normalize_question(question: str) -> str:
    """Normalize only for exact-text duplicate counting, not semantic deduplication."""

    normalized = unicodedata.normalize("NFKC", question).casefold()
    return re.sub(r"\W+", "", normalized)


def _audit_subset(subset_path: Path) -> MedquadSubsetAudit:
    question_counts: Counter[str] = Counter()
    counters: Counter[str] = Counter()
    xml_files = sorted(subset_path.rglob("*.xml"))
    for xml_path in xml_files:
        try:
            root = ET.parse(xml_path).getroot()
        except ET.ParseError:
            counters["malformed_xml_files"] += 1
            continue
        for pair in root.findall(".//QAPair"):
            question = (pair.findtext("Question") or "").strip()
            answer = (pair.findtext("Answer") or "").strip()
            counters["qa_pairs"] += 1
            counters["nonempty_answers" if answer else "empty_answers"] += 1
            key = normalize_question(question)
            if key:
                question_counts[key] += 1
            combined = f"{question}\n{answer}"
            counters["email_match_count"] += len(EMAIL_PATTERN.findall(combined))
            counters["phone_match_count"] += len(PHONE_PATTERN.findall(combined))

    return MedquadSubsetAudit(
        subset=subset_path.name,
        xml_files=len(xml_files),
        qa_pairs=counters["qa_pairs"],
        nonempty_answers=counters["nonempty_answers"],
        empty_answers=counters["empty_answers"],
        duplicate_question_instances=sum(count - 1 for count in question_counts.values()),
        email_match_count=counters["email_match_count"],
        phone_match_count=counters["phone_match_count"],
        malformed_xml_files=counters["malformed_xml_files"],
        answers_removed_upstream=subset_path.name in REMOVED_ANSWER_SUBSETS,
    )


def audit_medquad(repository_path: Path) -> dict[str, object]:
    """Return aggregate counts without copying questions, answers, or detected values."""

    subset_paths = sorted(
        path
        for path in repository_path.iterdir()
        if path.is_dir() and path.name[0].isdigit() and "_" in path.name
    )
    if not subset_paths:
        raise ValueError("No MedQuAD subset directories found.")
    subsets = [_audit_subset(path) for path in subset_paths]
    totals = {
        field: sum(getattr(subset, field) for subset in subsets)
        for field in (
            "xml_files",
            "qa_pairs",
            "nonempty_answers",
            "empty_answers",
            "duplicate_question_instances",
            "email_match_count",
            "phone_match_count",
            "malformed_xml_files",
        )
    }
    eligible_subsets = [
        subset.subset
        for subset in subsets
        if not subset.answers_removed_upstream
        and subset.nonempty_answers > 0
        and subset.malformed_xml_files == 0
    ]
    return {
        "status": "candidate_audit_only",
        "direct_triage_sft_eligible": False,
        "candidate_knowledge_subsets": eligible_subsets,
        "excluded_removed_answer_subsets": sorted(REMOVED_ANSWER_SUBSETS),
        "totals": totals,
        "subsets": [asdict(subset) for subset in subsets],
        "limits": [
            "Regex counts do not prove absence of personal data.",
            "Normalized duplicates do not detect semantic paraphrases.",
            "MedQuAD QA pairs do not contain clinically approved triage labels.",
        ],
    }


def audit_presidio_sample(
    repository_path: Path,
    anonymizer: AnonymizerLike,
    sample_per_subset: int = 10,
) -> dict[str, object]:
    """Run a deterministic, text-free Presidio audit on non-empty QA samples."""

    if sample_per_subset <= 0:
        raise ValueError("sample_per_subset must be positive.")
    aggregate_detected: Counter[str] = Counter()
    aggregate_residual: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    sampled_by_subset: dict[str, int] = {}
    selection_digests: list[str] = []

    for subset_path in sorted(repository_path.iterdir()):
        if (
            not subset_path.is_dir()
            or subset_path.name in REMOVED_ANSWER_SUBSETS
            or not subset_path.name[0].isdigit()
        ):
            continue
        candidates: list[tuple[str, str]] = []
        for xml_path in sorted(subset_path.rglob("*.xml")):
            try:
                root = ET.parse(xml_path).getroot()
            except ET.ParseError:
                continue
            relative_path = xml_path.relative_to(repository_path).as_posix()
            for pair in root.findall(".//QAPair"):
                question = (pair.findtext("Question") or "").strip()
                answer = (pair.findtext("Answer") or "").strip()
                if not question or not answer:
                    continue
                pair_id = pair.get("pid", "")
                digest = hashlib.sha256(f"{relative_path}:{pair_id}".encode()).hexdigest()
                candidates.append((digest, f"{question}\n{answer}"))
        selected = sorted(candidates, key=lambda item: item[0])[:sample_per_subset]
        sampled_by_subset[subset_path.name] = len(selected)
        for digest, text in selected:
            result = anonymizer.anonymize(text, "en")
            selection_digests.append(digest)
            aggregate_detected.update(result.audit.detected_entity_counts)
            aggregate_residual.update(result.audit.residual_entity_counts)
            status_counts[result.audit.status] += 1

    return {
        "status": "sample_audit_only",
        "language": "en",
        "sample_per_subset": sample_per_subset,
        "sample_count": sum(sampled_by_subset.values()),
        "sampled_by_subset": sampled_by_subset,
        "selection_sha256": hashlib.sha256("".join(selection_digests).encode()).hexdigest(),
        "detected_entity_counts": dict(sorted(aggregate_detected.items())),
        "residual_entity_counts": dict(sorted(aggregate_residual.items())),
        "anonymization_status_counts": dict(sorted(status_counts.items())),
        "limits": [
            "This deterministic sample is not a full-corpus PII scan.",
            "Detected values and source text are intentionally not persisted.",
            "A human review is still required before source admission.",
        ],
    }


def build_medquad_review_queue(
    repository_path: Path,
    anonymizer: AnonymizerLike,
    limit: int = 200,
    question_types: frozenset[str] = frozenset({"symptoms"}),
) -> dict[str, object]:
    """Build an anonymized authoring queue without inventing triage targets."""

    if limit <= 0:
        raise ValueError("limit must be positive.")
    candidates_by_subset: dict[str, list[tuple[str, dict[str, str]]]] = {}
    seen_questions: set[str] = set()
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
            for pair in root.findall(".//QAPair"):
                question_node = pair.find("Question")
                question = (question_node.text or "").strip() if question_node is not None else ""
                answer = (pair.findtext("Answer") or "").strip()
                question_type = question_node.get("qtype", "") if question_node is not None else ""
                normalized_key = normalize_question(question)
                if (
                    question_type not in question_types
                    or not question
                    or not answer
                    or not normalized_key
                    or normalized_key in seen_questions
                ):
                    continue
                seen_questions.add(normalized_key)
                pair_id = pair.get("pid", "")
                source_key = f"{relative_path}:{pair_id}"
                digest = hashlib.sha256(source_key.encode()).hexdigest()
                candidates_by_subset.setdefault(subset_path.name, []).append(
                    (
                        digest,
                        {
                            "source_record_id": digest,
                            "source_subset": subset_path.name,
                            "source_path": relative_path,
                            "source_pair_id": pair_id,
                            "question_type": question_type,
                            "question": question,
                            "answer": answer,
                        },
                    )
                )

    ordered_by_subset = {
        subset: sorted(candidates, key=lambda item: item[0])
        for subset, candidates in candidates_by_subset.items()
    }
    selected: list[tuple[str, dict[str, str]]] = []
    offset = 0
    while len(selected) < limit:
        added = False
        for subset in sorted(ordered_by_subset):
            candidates = ordered_by_subset[subset]
            if offset < len(candidates):
                selected.append(candidates[offset])
                added = True
                if len(selected) == limit:
                    break
        if not added:
            break
        offset += 1
    records = []
    rejected_residual_pii = 0
    detected_entities: Counter[str] = Counter()
    for _, candidate in selected:
        question_result = anonymizer.anonymize(candidate.pop("question"), "en")
        answer_result = anonymizer.anonymize(candidate.pop("answer"), "en")
        detected_entities.update(question_result.audit.detected_entity_counts)
        detected_entities.update(answer_result.audit.detected_entity_counts)
        if (
            question_result.audit.status != "passed"
            or answer_result.audit.status != "passed"
        ):
            rejected_residual_pii += 1
            continue
        records.append(
            {
                **candidate,
                "question": question_result.text,
                "answer": answer_result.text,
                "source_manifest_id": "src-medquad-577bd37",
                "license": "CC-BY-4.0",
                "allowed_use": "clinical_scenario_authoring_candidate_only",
                "clinical_review_status": "not_started",
                "triage_target": None,
            }
        )

    return {
        "status": "authoring_queue_not_training_data",
        "requested_limit": limit,
        "candidate_count_before_residual_check": len(selected),
        "record_count": len(records),
        "rejected_residual_pii": rejected_residual_pii,
        "question_types": sorted(question_types),
        "detected_entity_counts": dict(sorted(detected_entities.items())),
        "records": records,
        "limits": [
            "Records have no triage target and cannot enter SFT.",
            "Each derived clinical scenario requires independent clinical review.",
            "Anonymization may replace medical entities through false-positive detection.",
        ],
    }
