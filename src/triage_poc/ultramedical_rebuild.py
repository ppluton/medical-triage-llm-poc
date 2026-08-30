"""Deterministic, text-free split reconstruction for UltraMedical-Preference."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import BinaryIO

from triage_poc.ultramedical_audit import _conversation_text, _iter_split, normalize_text

SOURCE_MANIFEST_ID = "src-ultramedical-preference-761eb79"


def _prompt_hash(row: dict[str, object]) -> str:
    normalized = normalize_text(str(row.get("prompt", "")))
    return hashlib.sha256(normalized.encode()).hexdigest() if normalized else ""


def _preference_hash(row: dict[str, object]) -> str:
    payload = {
        "prompt": str(row.get("prompt", "")),
        "chosen": _conversation_text(row.get("chosen")),
        "rejected": _conversation_text(row.get("rejected")),
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


def _collect_prompt_hashes(path: Path, excluded: set[str] | None = None) -> set[str]:
    excluded = excluded or set()
    hashes: set[str] = set()
    for row in _iter_split(path):
        if not isinstance(row, dict):
            continue
        digest = _prompt_hash(row)
        if digest and digest not in excluded:
            hashes.add(digest)
    return hashes


def _write_index_line(output: BinaryIO, record: dict[str, object]) -> None:
    serialized = json.dumps(record, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    output.write((serialized + "\n").encode())


def rebuild_ultramedical_splits(data_directory: Path, output_path: Path) -> dict[str, object]:
    """Build a text-free decision index with test > dev > train split precedence."""

    paths = {split: data_directory / f"{split}.json" for split in ("train", "dev", "test")}
    missing = [path.name for path in paths.values() if not path.is_file()]
    if missing:
        raise ValueError(f"Missing required split files: {', '.join(sorted(missing))}")

    test_hashes = _collect_prompt_hashes(paths["test"])
    dev_hashes = _collect_prompt_hashes(paths["dev"], excluded=test_hashes)
    protected_hashes = test_hashes | dev_hashes
    output_path.parent.mkdir(parents=True, exist_ok=True)
    decisions: Counter[str] = Counter()
    source_rows: Counter[str] = Counter()
    unique_kept_prompts: dict[str, set[str]] = {
        "candidate_training": set(),
        "candidate_validation": set(),
        "reserved_evaluation": set(),
    }
    duplicate_preferences: Counter[str] = Counter()
    seen_preferences: dict[str, set[str]] = {split: set() for split in paths}

    with output_path.open("wb") as output:
        for split in ("train", "dev", "test"):
            for index, row in enumerate(_iter_split(paths[split])):
                source_rows[split] += 1
                if not isinstance(row, dict):
                    decision = "excluded_invalid_row"
                    prompt_digest = ""
                    preference_digest = ""
                    is_duplicate = False
                else:
                    prompt_digest = _prompt_hash(row)
                    preference_digest = _preference_hash(row)
                    is_duplicate = preference_digest in seen_preferences[split]
                    seen_preferences[split].add(preference_digest)
                    duplicate_preferences[split] += is_duplicate
                    if not prompt_digest:
                        decision = "excluded_empty_prompt"
                    elif split == "test":
                        decision = "reserved_evaluation"
                    elif prompt_digest in test_hashes:
                        decision = "excluded_test_overlap"
                    elif split == "dev":
                        decision = (
                            "excluded_exact_duplicate" if is_duplicate else "candidate_validation"
                        )
                    elif prompt_digest in protected_hashes:
                        decision = "excluded_dev_overlap"
                    else:
                        decision = (
                            "excluded_exact_duplicate" if is_duplicate else "candidate_training"
                        )

                decisions[decision] += 1
                if decision in unique_kept_prompts:
                    unique_kept_prompts[decision].add(prompt_digest)
                _write_index_line(
                    output,
                    {
                        "source_manifest_id": SOURCE_MANIFEST_ID,
                        "source_split": split,
                        "source_row_index": index,
                        "prompt_group_sha256": prompt_digest,
                        "preference_sha256": preference_digest,
                        "duplicate_preference_in_source_split": is_duplicate,
                        "decision": decision,
                        "clinical_review_status": (
                            "not_applicable" if decision == "reserved_evaluation" else "not_started"
                        ),
                    },
                )

    output_hasher = hashlib.sha256()
    with output_path.open("rb") as generated_index:
        for chunk in iter(lambda: generated_index.read(1024 * 1024), b""):
            output_hasher.update(chunk)
    output_sha256 = output_hasher.hexdigest()
    output_size = output_path.stat().st_size
    return {
        "status": "reconstruction_index_not_training_data",
        "source_manifest_id": SOURCE_MANIFEST_ID,
        "precedence": ["test", "dev", "train"],
        "source_rows": dict(source_rows),
        "decision_counts": dict(sorted(decisions.items())),
        "unique_kept_prompt_groups": {
            decision: len(hashes) for decision, hashes in unique_kept_prompts.items()
        },
        "duplicate_preference_instances": dict(duplicate_preferences),
        "protected_prompt_groups": {"test": len(test_hashes), "clean_dev": len(dev_hashes)},
        "output": {
            "path": str(output_path),
            "byte_size": output_size,
            "sha256": output_sha256,
            "contains_source_text": False,
        },
        "limits": [
            "Candidate decisions do not constitute clinical or PII approval.",
            "Normalized exact matching does not detect semantic paraphrases.",
            (
                "The index references source rows but intentionally contains no prompt "
                "or response text."
            ),
        ],
    }
