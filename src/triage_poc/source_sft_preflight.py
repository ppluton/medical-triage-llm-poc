"""Fail-closed checks for the source-derived SFT training artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


class SourceSftPreflightError(RuntimeError):
    """Raised when a source-derived SFT artifact is not safe to train."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise SourceSftPreflightError(
                    f"Invalid JSONL at {path.name}:{line_number}."
                ) from error
            if not isinstance(row, dict):
                raise SourceSftPreflightError(
                    f"Expected an object at {path.name}:{line_number}."
                )
            rows.append(row)
    return rows


def _validate_rendered(rows: list[dict[str, object]], split: str) -> set[str]:
    record_ids: set[str] = set()
    for row in rows:
        record_id = row.get("record_id")
        messages = row.get("messages")
        if not isinstance(record_id, str) or record_id in record_ids:
            raise SourceSftPreflightError(f"Duplicate or invalid {split} record_id.")
        if not isinstance(messages, list) or len(messages) != 3:
            raise SourceSftPreflightError(f"Invalid {split} conversation for {record_id}.")
        roles = [message.get("role") for message in messages if isinstance(message, dict)]
        contents = [message.get("content") for message in messages if isinstance(message, dict)]
        if roles != ["system", "user", "assistant"] or any(
            not isinstance(content, str) or not content.strip() for content in contents
        ):
            raise SourceSftPreflightError(f"Invalid {split} messages for {record_id}.")
        record_ids.add(record_id)
    return record_ids


def validate_source_sft_artifacts(
    manifest_path: Path, artifact_directory: Path
) -> tuple[
    dict[str, object],
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
]:
    """Validate hashes, counts, conversations, and test isolation."""

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "ready_for_local_educational_sft":
        raise SourceSftPreflightError("The derived dataset is not approved for local SFT.")
    if manifest.get("triage_label_count") != 0:
        raise SourceSftPreflightError("Source QA SFT must not contain triage labels.")

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        raise SourceSftPreflightError("Missing artifact inventory.")

    loaded: dict[str, list[dict[str, object]]] = {}
    for key in ("canonical", "train_qwen3", "validation_qwen3"):
        metadata = artifacts.get(key)
        if not isinstance(metadata, dict):
            raise SourceSftPreflightError(f"Missing {key} metadata.")
        path = artifact_directory / str(metadata.get("path", ""))
        if not path.is_file():
            raise SourceSftPreflightError(f"Missing artifact: {path.name}.")
        if _sha256(path) != metadata.get("sha256"):
            raise SourceSftPreflightError(f"Checksum mismatch: {path.name}.")
        rows = _read_jsonl(path)
        if len(rows) != metadata.get("record_count"):
            raise SourceSftPreflightError(f"Record-count mismatch: {path.name}.")
        loaded[key] = rows

    canonical = loaded["canonical"]
    train = loaded["train_qwen3"]
    validation = loaded["validation_qwen3"]
    train_ids = _validate_rendered(train, "train")
    validation_ids = _validate_rendered(validation, "validation")
    if train_ids & validation_ids:
        raise SourceSftPreflightError("Train and validation record IDs overlap.")
    canonical_splits = {
        str(record.get("record_id")): record.get("split") for record in canonical
    }
    test_ids = {record_id for record_id, split in canonical_splits.items() if split == "test"}
    if (train_ids | validation_ids) & test_ids:
        raise SourceSftPreflightError("The test split leaked into rendered training artifacts.")
    if any(canonical_splits.get(record_id) != "train" for record_id in train_ids):
        raise SourceSftPreflightError("A rendered train ID has the wrong canonical split.")
    if any(canonical_splits.get(record_id) != "validation" for record_id in validation_ids):
        raise SourceSftPreflightError("A rendered validation ID has the wrong canonical split.")
    return manifest, canonical, train, validation


def token_length_summary(
    rows: list[dict[str, object]], tokenizer, *, max_sequence_length: int
) -> dict[str, object]:
    """Measure a content-token proxy without claiming exact trainer packing."""

    lengths = []
    for row in rows:
        text = "\n".join(str(message["content"]) for message in row["messages"])
        lengths.append(len(tokenizer.encode(text, add_special_tokens=True)))
    ordered = sorted(lengths)

    def percentile(value: int) -> int:
        index = round((len(ordered) - 1) * value / 100)
        return ordered[index]

    return {
        "method": "concatenated_message_content_token_proxy",
        "count": len(lengths),
        "p50": percentile(50),
        "p90": percentile(90),
        "p95": percentile(95),
        "p99": percentile(99),
        "maximum": max(lengths),
        "over_max_sequence_length": sum(length > max_sequence_length for length in lengths),
        "max_sequence_length": max_sequence_length,
    }
