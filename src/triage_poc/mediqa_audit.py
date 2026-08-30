"""Privacy-minimizing inventory helpers for the candidate MEDIQA 2019 source."""

from __future__ import annotations

import hashlib
import re
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol

EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_PATTERN = re.compile(r"(?<!\d)(?:\+?1[ .-]?)?(?:\(?\d{3}\)?[ .-]?)\d{3}[ .-]\d{4}(?!\d)")
PLACEHOLDER_PATTERN = re.compile(r"\[(NAME|LOCATION|CONTACT)\]", re.IGNORECASE)


class AnonymizerLike(Protocol):
    def anonymize(self, text: str, language: str): ...


@dataclass(frozen=True)
class MediqaFileAudit:
    path: str
    task: str
    split: str
    canonical: bool
    labels_present: bool
    records: int
    answers: int
    positive_labels: int
    negative_labels: int
    answer_score_1: int
    answer_score_2: int
    answer_score_3: int
    answer_score_4: int
    placeholder_count: int
    email_match_count: int
    phone_match_count: int
    malformed_xml: bool


def normalize_text(text: str) -> str:
    """Normalize only for exact-text duplicate counting, not semantic matching."""

    normalized = unicodedata.normalize("NFKC", text).casefold()
    return re.sub(r"\W+", "", normalized)


def _describe_file(repository_path: Path, xml_path: Path) -> tuple[str, str, bool]:
    name = xml_path.name.lower()
    task = "rqe" if "task2-rqe" in name else "qa"
    if "training" in name:
        split = "train"
    elif "validation" in name:
        split = "validation"
    elif "test" in name:
        split = "test"
    else:
        split = "unknown"
    labeled_peer = xml_path.with_name(xml_path.stem + "-wLabels.xml")
    canonical = not (split == "test" and "-wlabels" not in name and labeled_peer.exists())
    return task, split, canonical


def _iter_record_texts(root: ET.Element, task: str):
    if task == "rqe":
        for pair in root.findall(".//pair"):
            yield "\n".join(
                ((pair.findtext("chq") or "").strip(), (pair.findtext("faq") or "").strip())
            )
    else:
        for question in root.findall(".//Question"):
            parts = [(question.findtext("QuestionText") or "").strip()]
            parts.extend(
                (answer.findtext("AnswerText") or "").strip()
                for answer in question.findall(".//Answer")
            )
            yield "\n".join(part for part in parts if part)


def _audit_file(repository_path: Path, xml_path: Path) -> MediqaFileAudit:
    task, split, canonical = _describe_file(repository_path, xml_path)
    relative_path = xml_path.relative_to(repository_path).as_posix()
    try:
        root = ET.parse(xml_path).getroot()
    except ET.ParseError:
        return MediqaFileAudit(
            path=relative_path,
            task=task,
            split=split,
            canonical=canonical,
            labels_present=False,
            records=0,
            answers=0,
            positive_labels=0,
            negative_labels=0,
            answer_score_1=0,
            answer_score_2=0,
            answer_score_3=0,
            answer_score_4=0,
            placeholder_count=0,
            email_match_count=0,
            phone_match_count=0,
            malformed_xml=True,
        )

    pairs = root.findall(".//pair")
    questions = root.findall(".//Question")
    answers = root.findall(".//Answer")
    values = Counter(pair.get("value") for pair in pairs)
    scores = Counter(answer.get("ReferenceScore") for answer in answers)
    combined = "\n".join(_iter_record_texts(root, task))
    return MediqaFileAudit(
        path=relative_path,
        task=task,
        split=split,
        canonical=canonical,
        labels_present=all(pair.get("value") in {"true", "false"} for pair in pairs)
        if task == "rqe"
        else all(answer.get("ReferenceScore") in {"1", "2", "3", "4"} for answer in answers),
        records=len(pairs) if task == "rqe" else len(questions),
        answers=len(answers),
        positive_labels=values["true"],
        negative_labels=values["false"],
        answer_score_1=scores["1"],
        answer_score_2=scores["2"],
        answer_score_3=scores["3"],
        answer_score_4=scores["4"],
        placeholder_count=len(PLACEHOLDER_PATTERN.findall(combined)),
        email_match_count=len(EMAIL_PATTERN.findall(combined)),
        phone_match_count=len(PHONE_PATTERN.findall(combined)),
        malformed_xml=False,
    )


def audit_mediqa(repository_path: Path) -> dict[str, object]:
    """Return canonical corpus counts without returning any source record text."""

    xml_files = sorted(repository_path.rglob("*.xml"))
    if not xml_files:
        raise ValueError("No MEDIQA XML files found.")
    files = [_audit_file(repository_path, path) for path in xml_files]
    canonical_files = [file for file in files if file.canonical]
    totals = {
        field: sum(getattr(file, field) for file in canonical_files)
        for field in (
            "records",
            "answers",
            "positive_labels",
            "negative_labels",
            "answer_score_1",
            "answer_score_2",
            "answer_score_3",
            "answer_score_4",
            "placeholder_count",
            "email_match_count",
            "phone_match_count",
        )
    }
    totals["malformed_xml_files"] = sum(file.malformed_xml for file in canonical_files)

    duplicate_counters: dict[str, Counter[str]] = {
        "rqe_chq": Counter(),
        "rqe_pair": Counter(),
        "qa_question": Counter(),
    }
    for xml_path in xml_files:
        task, _, canonical = _describe_file(repository_path, xml_path)
        if not canonical:
            continue
        try:
            root = ET.parse(xml_path).getroot()
        except ET.ParseError:
            continue
        if task == "rqe":
            for pair in root.findall(".//pair"):
                chq = normalize_text(pair.findtext("chq") or "")
                faq = normalize_text(pair.findtext("faq") or "")
                if chq:
                    duplicate_counters["rqe_chq"][chq] += 1
                if chq or faq:
                    duplicate_counters["rqe_pair"][f"{chq}:{faq}"] += 1
        else:
            for question in root.findall(".//Question"):
                key = normalize_text(question.findtext("QuestionText") or "")
                if key:
                    duplicate_counters["qa_question"][key] += 1

    duplicate_instances = {
        field: sum(count - 1 for count in counter.values())
        for field, counter in duplicate_counters.items()
    }
    return {
        "status": "candidate_audit_only",
        "direct_triage_sft_eligible": False,
        "task1_mednli_included": False,
        "canonical_policy": (
            "Prefer labeled test exports and exclude their unlabeled duplicates from totals."
        ),
        "totals": totals,
        "duplicate_instances": duplicate_instances,
        "files": [asdict(file) for file in files],
        "limits": [
            "Regex and placeholder counts do not prove absence of personal data.",
            "Normalized duplicates do not detect semantic paraphrases or cross-source leakage.",
            "MEDIQA RQE and QA labels are not clinically approved triage targets.",
            "Task 1 MedNLI is controlled by PhysioNet and was not acquired.",
        ],
    }


def audit_presidio_question_sample(
    repository_path: Path,
    anonymizer: AnonymizerLike,
    sample_per_file: int = 10,
) -> dict[str, object]:
    """Audit a deterministic question-only sample without persisting detected values."""

    if sample_per_file <= 0:
        raise ValueError("sample_per_file must be positive.")
    detected: Counter[str] = Counter()
    residual: Counter[str] = Counter()
    statuses: Counter[str] = Counter()
    sampled_by_file: dict[str, int] = {}
    digests: list[str] = []

    for xml_path in sorted(repository_path.rglob("*.xml")):
        task, _, canonical = _describe_file(repository_path, xml_path)
        if not canonical:
            continue
        try:
            root = ET.parse(xml_path).getroot()
        except ET.ParseError:
            continue
        relative_path = xml_path.relative_to(repository_path).as_posix()
        candidates: list[tuple[str, str]] = []
        if task == "rqe":
            for pair in root.findall(".//pair"):
                record_id = pair.get("pid", "")
                text = "\n".join(
                    ((pair.findtext("chq") or "").strip(), (pair.findtext("faq") or "").strip())
                )
                digest = hashlib.sha256(f"{relative_path}:{record_id}".encode()).hexdigest()
                if text.strip():
                    candidates.append((digest, text))
        else:
            for question in root.findall(".//Question"):
                record_id = question.get("QID", "")
                text = (question.findtext("QuestionText") or "").strip()
                digest = hashlib.sha256(f"{relative_path}:{record_id}".encode()).hexdigest()
                if text:
                    candidates.append((digest, text))

        selected = sorted(candidates, key=lambda item: item[0])[:sample_per_file]
        sampled_by_file[relative_path] = len(selected)
        for digest, text in selected:
            result = anonymizer.anonymize(text, "en")
            digests.append(digest)
            detected.update(result.audit.detected_entity_counts)
            residual.update(result.audit.residual_entity_counts)
            statuses[result.audit.status] += 1

    return {
        "status": "sample_audit_only",
        "language": "en",
        "sample_scope": "consumer_and_reference_questions_only",
        "sample_per_file": sample_per_file,
        "sample_count": sum(sampled_by_file.values()),
        "sampled_by_file": sampled_by_file,
        "selection_sha256": hashlib.sha256("".join(digests).encode()).hexdigest(),
        "detected_entity_counts": dict(sorted(detected.items())),
        "residual_entity_counts": dict(sorted(residual.items())),
        "anonymization_status_counts": dict(sorted(statuses.items())),
        "limits": [
            "This deterministic sample is not a full-corpus PII scan.",
            "Answer texts were excluded from this privacy sample.",
            "Detected values and source text are intentionally not persisted.",
            "A human review is required before source admission.",
        ],
    }
