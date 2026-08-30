"""Prevent training runs when governed source manifests are not approved."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path


class TrainingPreflightError(RuntimeError):
    pass


def require_approved_manifests(
    manifest_directory: Path, manifest_names: Iterable[str] | None = None
) -> list[str]:
    """Require all manifests, or an explicit governed subset, to be approved."""

    if manifest_names is None:
        manifests = sorted(manifest_directory.glob("src-*.json"))
    else:
        names = sorted(set(manifest_names))
        manifests = [manifest_directory / name for name in names]
        missing = [path.name for path in manifests if not path.is_file()]
        if missing:
            raise TrainingPreflightError(f"Selected manifests not found: {', '.join(missing)}")
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
