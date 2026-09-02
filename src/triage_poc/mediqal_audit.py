"""Text-minimizing inventory checks for the candidate MediQAl source."""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from collections.abc import Iterator
from pathlib import Path

CONFIGS = ("mcqu", "mcqm", "oeq")
SPLITS = ("train", "validation", "test")


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return re.sub(r"\W+", "", normalized)


def iter_rows(repository_path: Path) -> Iterator[tuple[str, str, int, dict[str, object]]]:
    for config_name in CONFIGS:
        for split in SPLITS:
            source_path = repository_path / config_name / f"{split}.json"
            if not source_path.is_file():
                continue
            with source_path.open(encoding="utf-8") as stream:
                for line_number, line in enumerate(stream, start=1):
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError as error:
                        raise ValueError(
                            f"Invalid JSONL at {source_path}:{line_number}."
                        ) from error
                    if not isinstance(row, dict):
                        raise ValueError(
                            f"Expected a JSON object at {source_path}:{line_number}."
                        )
                    yield config_name, split, line_number, row


def audit_mediqal(repository_path: Path) -> dict[str, object]:
    counts: Counter[str] = Counter()
    missing_required_fields: Counter[str] = Counter()
    normalized_questions: dict[str, set[str]] = {split: set() for split in SPLITS}
    record_keys: set[str] = set()
    duplicate_record_keys = 0

    for config_name, split, line_number, row in iter_rows(repository_path):
        counts[f"{config_name}/{split}"] += 1
        source_id = str(row.get("id") or "").strip()
        record_key = f"{config_name}:{split}:{source_id or line_number}"
        if record_key in record_keys:
            duplicate_record_keys += 1
        record_keys.add(record_key)

        question = str(row.get("question") or "").strip()
        if not source_id:
            missing_required_fields["id"] += 1
        if not question:
            missing_required_fields["question"] += 1
        if config_name in {"mcqu", "mcqm"} and not str(
            row.get("correct_answers") or ""
        ).strip():
            missing_required_fields["correct_answers"] += 1
        normalized = normalize_text(question)
        if normalized:
            normalized_questions[split].add(normalized)

    split_overlaps = {
        "train_validation": len(
            normalized_questions["train"] & normalized_questions["validation"]
        ),
        "train_test": len(normalized_questions["train"] & normalized_questions["test"]),
        "validation_test": len(
            normalized_questions["validation"] & normalized_questions["test"]
        ),
    }
    return {
        "dataset": "ANR-MALADES/MediQAl",
        "status": "candidate_not_training_data",
        "counts": dict(sorted(counts.items())),
        "total_rows": sum(counts.values()),
        "authoring_eligible_rows": sum(
            count
            for key, count in counts.items()
            if key.split("/", 1)[1] in {"train", "validation"}
        ),
        "test_rows_excluded_from_authoring": sum(
            count for key, count in counts.items() if key.endswith("/test")
        ),
        "missing_required_fields": dict(sorted(missing_required_fields.items())),
        "duplicate_record_keys": duplicate_record_keys,
        "normalized_question_split_overlaps": split_overlaps,
        "direct_triage_sft_eligible": False,
        "limits": [
            "Correct MCQ answers are not clinically approved triage priorities.",
            "Normalized question matching does not detect semantic paraphrases.",
            "This inventory does not establish full-corpus PII absence or clinical validity.",
        ],
    }
