"""Fail-closed checks for the source-derived SFT training artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from triage_poc.source_sft import render_source_sft_conversation


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
    canonical_ids = [record.get("record_id") for record in canonical]
    if any(not isinstance(value, str) or not value for value in canonical_ids):
        raise SourceSftPreflightError("Invalid canonical record ID.")
    if len(set(canonical_ids)) != len(canonical_ids):
        raise SourceSftPreflightError("Duplicate canonical record ID.")
    if any(record.get("split") not in {"train", "validation", "test"} for record in canonical):
        raise SourceSftPreflightError("Invalid canonical split.")
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
    for split, rendered_ids in (("train", train_ids), ("validation", validation_ids)):
        expected_ids = {key for key, value in canonical_splits.items() if value == split}
        if not expected_ids or rendered_ids != expected_ids:
            raise SourceSftPreflightError(f"Rendered {split} does not cover its canonical split.")
    canonical_by_id = {record["record_id"]: record for record in canonical}
    for row in train + validation:
        if row != render_source_sft_conversation(canonical_by_id[row["record_id"]]):
            raise SourceSftPreflightError("Rendered content differs from its canonical record.")
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


def rendered_token_summary(rows, tokenizer, *, max_sequence_length: int) -> dict:
    """Inspect exact trainer text, including template overhead and terminal EOS."""
    if not rows or max_sequence_length <= 0 or tokenizer.eos_token_id is None:
        raise SourceSftPreflightError("Rows, positive context size and EOS are required.")
    lengths = []
    missing_eos = 0
    for row in rows:
        text = tokenizer.apply_chat_template(row["messages"], tokenize=False,
                                             add_generation_prompt=False)
        ids = tokenizer.encode(text, add_special_tokens=False)
        lengths.append(len(ids))
        missing_eos += not ids or ids[-1] != tokenizer.eos_token_id
    return {"method": "exact_training_chat_template", "count": len(rows),
            "maximum": max(lengths), "max_sequence_length": max_sequence_length,
            "over_max_sequence_length": sum(n > max_sequence_length for n in lengths),
            "missing_terminal_native_eos": missing_eos,
            "pad_equals_eos": tokenizer.pad_token_id == tokenizer.eos_token_id}


def preflight_failures(summaries: dict) -> list[str]:
    failures = []
    for split, summary in summaries.items():
        if summary["over_max_sequence_length"]:
            failures.append(f"{split}: rendered sequences exceed the context limit")
        if summary["missing_terminal_native_eos"]:
            failures.append(f"{split}: native EOS is not the terminal training token")
        if summary["pad_equals_eos"]:
            failures.append(f"{split}: padding can mask EOS targets")
    return failures
