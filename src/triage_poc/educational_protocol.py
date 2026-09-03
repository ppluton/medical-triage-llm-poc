"""Validation helpers for the educational-only triage protocol."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


class EducationalProtocolError(ValueError):
    """Raised when the educational protocol could enable unsafe or misleading use."""


def load_educational_protocol(protocol_path: Path, schema_path: Path) -> dict[str, Any]:
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(schema).iter_errors(protocol),
        key=lambda error: list(error.path),
    )
    if errors:
        messages = "; ".join(error.message for error in errors)
        raise EducationalProtocolError(f"Protocol schema validation failed: {messages}")

    split_total = sum(protocol["dataset_plan"]["split_counts"].values())
    if split_total != protocol["dataset_plan"]["total_records"]:
        raise EducationalProtocolError("Dataset split counts do not match total_records.")
    if protocol["clinical_validation"]["performed"]:
        raise EducationalProtocolError(
            "Educational protocol must not claim clinical validation."
        )
    if protocol["uncertainty_policy"]["deferred_due_to_missing_information_allowed"]:
        raise EducationalProtocolError(
            "Missing information must never be the sole reason for deferred triage."
        )
    return protocol
