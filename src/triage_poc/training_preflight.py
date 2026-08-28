"""Prevent training runs when governed source manifests are not approved."""

from __future__ import annotations

import json
from pathlib import Path


class TrainingPreflightError(RuntimeError):
    pass


def require_approved_manifests(manifest_directory: Path) -> list[str]:
    manifests = sorted(manifest_directory.glob("src-*.json"))
    if not manifests:
        raise TrainingPreflightError("No approved source manifests are available for training.")
    rejected = []
    for path in manifests:
        status = json.loads(path.read_text(encoding="utf-8")).get("admission_status")
        if status != "approved":
            rejected.append(path.name)
    if rejected:
        raise TrainingPreflightError(f"Non-approved manifests: {', '.join(rejected)}")
    return [path.name for path in manifests]
