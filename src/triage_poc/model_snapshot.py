"""Checksum-locked identity verification for the attached base-model snapshot."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

EXPECTED_BASE_REVISION = "e249956c10337100486d07afb77e3eb2b30906b8"
EXPECTED_BASE_MODEL_SHA256 = "6df85b39330e5a425ee36253d0f894e4387e4f0a15b9c53cb467d668e6b3a841"
EXPECTED_BASE_MANIFEST_SHA256 = "920a5897431d1dfc62502815c5ec4929a149d5f324e6f5b2b3d86db4a691f0d1"
BASE_SERVED_MODEL_NAME = "qwen3-base-e249956c"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_base_snapshot(
    model_directory: Path,
    *,
    expected_manifest_sha256: str = EXPECTED_BASE_MANIFEST_SHA256,
    expected_model_sha256: str = EXPECTED_BASE_MODEL_SHA256,
) -> dict:
    """Fail closed unless the attached model snapshot matches every recorded checksum."""
    model_directory = Path(model_directory)
    manifest_path = model_directory / "MODEL_SNAPSHOT_MANIFEST.json"
    if sha256(manifest_path) != expected_manifest_sha256:
        raise ValueError("Unexpected base-model manifest checksum")
    manifest = json.loads(manifest_path.read_text())
    if (
        manifest.get("source", {}).get("revision") != EXPECTED_BASE_REVISION
        or manifest.get("model_sha256") != expected_model_sha256
        or manifest.get("license", {}).get("spdx") != "Apache-2.0"
    ):
        raise ValueError("Unexpected base-model identity or license")
    files = manifest.get("files")
    if not isinstance(files, dict) or "model.safetensors" not in files:
        raise ValueError("Incomplete base-model manifest")
    for name, expected in files.items():
        path = model_directory / name
        if (
            not path.is_file()
            or path.stat().st_size != expected.get("size")
            or sha256(path) != expected.get("sha256")
        ):
            raise ValueError(f"Base-model snapshot checksum mismatch: {name}")
    return {
        "revision": EXPECTED_BASE_REVISION,
        "model_sha256": expected_model_sha256,
        "manifest_sha256": expected_manifest_sha256,
        "license": "Apache-2.0",
        "files_verified": len(files),
    }
