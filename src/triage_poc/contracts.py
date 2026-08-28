"""Validation helpers for tracked manifests and synthetic record contracts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
MANIFESTS_DIRECTORY = REPOSITORY_ROOT / "data" / "manifests"


class ContractValidationError(ValueError):
    """Raised when a tracked data-contract document is invalid."""


def validate_against_schema(instance: dict[str, Any], schema_name: str) -> None:
    """Validate an in-memory record and report all schema errors without logging its content."""

    schema_path = MANIFESTS_DIRECTORY / schema_name
    if not schema_path.is_file():
        raise ContractValidationError(f"Schema not found: {schema_name}")

    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ContractValidationError(f"Schema is not valid JSON: {schema_name}") from exc

    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.path))
    if errors:
        summary = "; ".join(error.message for error in errors)
        raise ContractValidationError(f"Contract validation failed: {summary}")
