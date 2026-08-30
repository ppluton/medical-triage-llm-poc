"""Build bounded SFT conversation records from the canonical triage contract."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from typing import Any

from triage_poc.contracts import ContractValidationError, validate_against_schema

SYSTEM_PROMPT = (
    "You are a medical-triage assistance proof of concept. You do not diagnose, "
    "prescribe, or replace a healthcare professional. Return only the requested JSON "
    "triage structure and preserve its safety notice."
)


class SftDatasetError(ValueError):
    """Raised when a record cannot safely enter the SFT preparation flow."""


def _context_to_json(context: Mapping[str, Any]) -> str:
    return json.dumps(context, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def render_sft_conversation(record: Mapping[str, Any]) -> dict[str, Any]:
    """Render one train or validation SFT record without inventing clinical content."""

    try:
        validate_against_schema(dict(record), "triage_record_v1.schema.json")
    except ContractValidationError as error:
        raise SftDatasetError(f"Invalid triage record: {error}") from error

    if record["task_type"] != "sft":
        raise SftDatasetError("Only task_type 'sft' can be rendered for SFT.")
    if record["split"] not in {"train", "validation"}:
        raise SftDatasetError("The isolated test split must never enter SFT preparation.")

    return {
        "record_id": record["record_id"],
        "language": record["language"],
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Patient context (structured JSON): "
                    + _context_to_json(record["patient_context"])
                ),
            },
            {
                "role": "assistant",
                "content": json.dumps(record["sft_target"], ensure_ascii=False, sort_keys=True),
            },
        ],
    }


def render_sft_dataset(records: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Render records while preventing duplicate identifiers from hiding data mistakes."""

    rendered = [render_sft_conversation(record) for record in records]
    identifiers = [record["record_id"] for record in rendered]
    if len(identifiers) != len(set(identifiers)):
        raise SftDatasetError("SFT record identifiers must be unique.")
    return rendered


def render_qwen3_text_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """Render one canonical SFT record as a preformatted Qwen3 text sequence.

    This is limited to the Desktop micro-run path. Qwen3 Base does not include a
    tokenizer chat template, so the sequence follows Unsloth's named ``qwen3``
    template, including its empty thinking block before a final assistant answer.
    """

    conversation = render_sft_conversation(record)
    system, user, assistant = conversation["messages"]
    text = (
        f"<|im_start|>system\n{system['content']}<|im_end|>\n"
        f"<|im_start|>user\n{user['content']}<|im_end|>\n"
        f"<|im_start|>assistant\n<think>\n\n</think>\n\n"
        f"{assistant['content']}<|im_end|>\n"
    )
    return {
        "record_id": conversation["record_id"],
        "language": conversation["language"],
        "text": text,
    }


def render_qwen3_text_dataset(records: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Render unique SFT records to preformatted Qwen3 training text."""

    rendered = [render_qwen3_text_record(record) for record in records]
    identifiers = [record["record_id"] for record in rendered]
    if len(identifiers) != len(set(identifiers)):
        raise SftDatasetError("SFT record identifiers must be unique.")
    return rendered
