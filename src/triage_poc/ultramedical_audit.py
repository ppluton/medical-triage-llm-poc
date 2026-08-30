"""Text-free audit helpers for UltraMedical-Preference JSON splits."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections import Counter
from collections.abc import Iterator
from pathlib import Path
from typing import Protocol

import ijson

EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_PATTERN = re.compile(r"(?<!\d)(?:\+?1[ .-]?)?(?:\(?\d{3}\)?[ .-]?)\d{3}[ .-]\d{4}(?!\d)")
REQUIRED_KEYS = {"prompt_id", "label_type", "prompt", "chosen", "rejected", "metadata"}


class AnonymizerLike(Protocol):
    def anonymize(self, text: str, language: str): ...


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return re.sub(r"\W+", "", normalized)


def _iter_split(path: Path) -> Iterator[object]:
    """Stream array rows so the approximately 1 GB train split stays memory-bounded."""

    try:
        with path.open("rb") as source:
            yield from ijson.items(source, "item")
    except ijson.JSONError as exc:
        raise ValueError(f"Invalid JSON split: {path.name}") from exc


def _conversation_roles(value: object) -> tuple[str | None, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(message.get("role") if isinstance(message, dict) else None for message in value)


def _conversation_text(value: object) -> str:
    if not isinstance(value, list):
        return ""
    return "\n".join(
        str(message.get("content", ""))
        for message in value
        if isinstance(message, dict)
    )


def _audit_split(path: Path) -> tuple[dict[str, object], set[str]]:
    labels: Counter[str] = Counter()
    source_datasets: Counter[str] = Counter()
    chosen_models: Counter[str] = Counter()
    rejected_models: Counter[str] = Counter()
    prompt_ids: Counter[str] = Counter()
    prompt_hashes: Counter[str] = Counter()
    counters: Counter[str] = Counter()

    for row in _iter_split(path):
        counters["rows"] += 1
        if not isinstance(row, dict):
            counters["invalid_row_type"] += 1
            continue
        missing = REQUIRED_KEYS - row.keys()
        counters["rows_missing_required_keys"] += bool(missing)
        label = str(row.get("label_type", ""))
        labels[label] += 1
        prompt_id = str(row.get("prompt_id", ""))
        prompt_ids[prompt_id] += 1
        source_datasets[prompt_id.split(",", 1)[0] or "unknown"] += 1
        prompt = str(row.get("prompt", ""))
        normalized_prompt = normalize_text(prompt)
        if normalized_prompt:
            prompt_hashes[hashlib.sha256(normalized_prompt.encode()).hexdigest()] += 1
        chosen = row.get("chosen")
        rejected = row.get("rejected")
        counters["invalid_chosen_roles"] += _conversation_roles(chosen) != ("user", "assistant")
        counters["invalid_rejected_roles"] += _conversation_roles(rejected) != ("user", "assistant")
        chosen_text = _conversation_text(chosen)
        rejected_text = _conversation_text(rejected)
        counters["identical_chosen_rejected"] += chosen_text == rejected_text
        chosen_user = chosen[0].get("content", "") if isinstance(chosen, list) and chosen else ""
        rejected_user = (
            rejected[0].get("content", "") if isinstance(rejected, list) and rejected else ""
        )
        counters["prompt_conversation_mismatch"] += prompt not in {chosen_user, rejected_user}
        combined = "\n".join((prompt, chosen_text, rejected_text))
        counters["email_match_count"] += len(EMAIL_PATTERN.findall(combined))
        counters["phone_match_count"] += len(PHONE_PATTERN.findall(combined))
        metadata = row.get("metadata")
        if not isinstance(metadata, dict):
            counters["invalid_metadata"] += 1
            continue
        chosen_metadata = metadata.get("chosen")
        rejected_metadata = metadata.get("rejected")
        if isinstance(chosen_metadata, dict):
            chosen_models[str(chosen_metadata.get("model", "unknown"))] += 1
        if isinstance(rejected_metadata, dict):
            rejected_models[str(rejected_metadata.get("model", "unknown"))] += 1

    report = {
        "path": path.name,
        "rows": counters["rows"],
        "label_type_counts": dict(sorted(labels.items())),
        "source_dataset_counts": dict(sorted(source_datasets.items())),
        "chosen_model_counts": dict(sorted(chosen_models.items())),
        "rejected_model_counts": dict(sorted(rejected_models.items())),
        "duplicate_prompt_id_instances": sum(count - 1 for count in prompt_ids.values()),
        "duplicate_normalized_prompt_instances": sum(
            count - 1 for count in prompt_hashes.values()
        ),
        "rows_missing_required_keys": counters["rows_missing_required_keys"],
        "invalid_row_type": counters["invalid_row_type"],
        "invalid_chosen_roles": counters["invalid_chosen_roles"],
        "invalid_rejected_roles": counters["invalid_rejected_roles"],
        "identical_chosen_rejected": counters["identical_chosen_rejected"],
        "prompt_conversation_mismatch": counters["prompt_conversation_mismatch"],
        "invalid_metadata": counters["invalid_metadata"],
        "email_match_count": counters["email_match_count"],
        "phone_match_count": counters["phone_match_count"],
    }
    return report, set(prompt_hashes)


def audit_ultramedical_preference(data_directory: Path) -> dict[str, object]:
    """Audit available splits and preserve the human-revised test as evaluation-only."""

    required_paths = {split: data_directory / f"{split}.json" for split in ("dev", "test")}
    missing = [path.name for path in required_paths.values() if not path.is_file()]
    if missing:
        raise ValueError(f"Missing required split files: {', '.join(sorted(missing))}")
    split_reports: dict[str, dict[str, object]] = {}
    prompt_hashes: dict[str, set[str]] = {}
    split_paths = dict(required_paths)
    train_path = data_directory / "train.json"
    if train_path.is_file():
        split_paths = {"train": train_path, **split_paths}
    for split, path in split_paths.items():
        split_reports[split], prompt_hashes[split] = _audit_split(path)
    overlaps = {
        f"{left}_{right}": len(prompt_hashes[left] & prompt_hashes[right])
        for index, left in enumerate(split_paths)
        for right in list(split_paths)[index + 1 :]
    }
    allowed_split_use = {"dev": "candidate_validation_only", "test": "evaluation_only"}
    if "train" in split_paths:
        allowed_split_use = {"train": "candidate_training_only", **allowed_split_use}
    return {
        "status": "candidate_audit_only",
        "direct_triage_dpo_eligible": False,
        "download_scope": list(split_paths),
        "train_downloaded": "train" in split_paths,
        "allowed_split_use": allowed_split_use,
        "cross_split_normalized_prompt_overlap": overlaps,
        "splits": split_reports,
        "limits": [
            (
                "Downloaded rows remain candidates until PII, leakage, quality, "
                "and triage checks pass."
            ),
            "Preference quality and biomedical relevance do not establish triage safety.",
            "Regex counts do not prove absence of personal data.",
            "The human-revised test split must never be used for optimization.",
        ],
    }


def audit_presidio_preference_sample(
    data_directory: Path,
    anonymizer: AnonymizerLike,
    sample_per_split: int = 10,
) -> dict[str, object]:
    """Run a deterministic, text-free PII audit over complete preference triples."""

    if sample_per_split <= 0:
        raise ValueError("sample_per_split must be positive.")
    detected: Counter[str] = Counter()
    residual: Counter[str] = Counter()
    statuses: Counter[str] = Counter()
    sampled_by_split: dict[str, int] = {}
    digests: list[str] = []
    splits = [
        split
        for split in ("train", "dev", "test")
        if (data_directory / f"{split}.json").is_file()
    ]
    for split in splits:
        candidates: list[tuple[str, str]] = []
        for index, row in enumerate(_iter_split(data_directory / f"{split}.json")):
            if not isinstance(row, dict):
                continue
            record_id = str(row.get("prompt_id", index))
            digest = hashlib.sha256(f"{split}:{index}:{record_id}".encode()).hexdigest()
            text = "\n".join(
                (
                    str(row.get("prompt", "")),
                    _conversation_text(row.get("chosen")),
                    _conversation_text(row.get("rejected")),
                )
            )
            if text.strip():
                if len(candidates) < sample_per_split or digest < candidates[-1][0]:
                    candidates.append((digest, text))
                    candidates.sort(key=lambda item: item[0])
                    del candidates[sample_per_split:]
        selected = candidates
        sampled_by_split[split] = len(selected)
        for digest, text in selected:
            result = anonymizer.anonymize(text, "en")
            digests.append(digest)
            detected.update(result.audit.detected_entity_counts)
            residual.update(result.audit.residual_entity_counts)
            statuses[result.audit.status] += 1
    return {
        "status": "sample_audit_only",
        "language": "en",
        "sample_scope": "prompt_chosen_rejected",
        "sample_per_split": sample_per_split,
        "sample_count": sum(sampled_by_split.values()),
        "sampled_by_split": sampled_by_split,
        "selection_sha256": hashlib.sha256("".join(digests).encode()).hexdigest(),
        "detected_entity_counts": dict(sorted(detected.items())),
        "residual_entity_counts": dict(sorted(residual.items())),
        "anonymization_status_counts": dict(sorted(statuses.items())),
        "limits": [
            "This deterministic sample is not a full-corpus PII scan.",
            "Detected values and source text are intentionally not persisted.",
            "A clinical and quality review is required before DPO admission.",
        ],
    }
