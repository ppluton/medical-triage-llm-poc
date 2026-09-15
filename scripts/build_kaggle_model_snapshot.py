#!/usr/bin/env python3
"""Build a checksum-locked private Kaggle dataset from an exact HF model snapshot."""

from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
import re
import shutil
from pathlib import Path

REQUIRED_FILES = (
    ".gitattributes",
    "README.md",
    "added_tokens.json",
    "config.json",
    "generation_config.json",
    "merges.txt",
    "model.safetensors",
    "special_tokens_map.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "vocab.json",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _materialize(source: Path, destination: Path) -> str:
    resolved = source.resolve(strict=True)
    try:
        os.link(resolved, destination)
        return "hardlink"
    except OSError as error:
        if error.errno not in {errno.EXDEV, errno.EPERM, errno.EACCES}:
            raise
        shutil.copy2(resolved, destination)
        return "copy"


def build_snapshot(
    snapshot: Path,
    output: Path,
    *,
    revision: str,
    expected_model_sha256: str,
    dataset_id: str,
) -> dict:
    """Validate, materialize and manifest one immutable model snapshot."""
    if output.exists():
        raise ValueError("Choose a fresh output directory.")
    if not re.fullmatch(r"[0-9a-f]{40}", revision) or snapshot.name != revision:
        raise ValueError("Snapshot directory must match the exact 40-character revision.")
    if not re.fullmatch(r"[0-9a-f]{64}", expected_model_sha256):
        raise ValueError("Expected model checksum must be a SHA-256 digest.")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9-]{2,49}", dataset_id):
        raise ValueError("Expected a bounded Kaggle owner/dataset identifier.")

    missing = [name for name in REQUIRED_FILES if not (snapshot / name).is_file()]
    if missing:
        raise ValueError(f"Snapshot is incomplete: {missing}.")
    readme = (snapshot / "README.md").read_text()
    if not re.search(r"(?m)^license:\s*apache-2\.0\s*$", readme):
        raise ValueError("Snapshot model card does not declare Apache-2.0.")
    if "Qwen/Qwen3-1.7B-Base" not in readme:
        raise ValueError("Snapshot model card does not identify the expected upstream base.")

    files = {}
    for name in REQUIRED_FILES:
        path = snapshot / name
        files[name] = {"size": path.stat().st_size, "sha256": sha256(path)}
    if files["model.safetensors"]["sha256"] != expected_model_sha256:
        raise ValueError("Model checksum mismatch; refusing to prepare upload.")

    output.mkdir(parents=True)
    materialization = {}
    for name in REQUIRED_FILES:
        materialization[name] = _materialize(snapshot / name, output / name)
    manifest = {
        "schema_version": "1.0.0",
        "status": "verified_snapshot_for_private_kaggle",
        "source": {
            "repository": "unsloth/Qwen3-1.7B-Base",
            "upstream_base": "Qwen/Qwen3-1.7B-Base",
            "revision": revision,
            "url": f"https://huggingface.co/unsloth/Qwen3-1.7B-Base/tree/{revision}",
        },
        "license": {
            "spdx": "Apache-2.0",
            "declared_in": "README.md",
            "url": "https://www.apache.org/licenses/LICENSE-2.0",
        },
        "dataset_id": dataset_id,
        "model_sha256": expected_model_sha256,
        "files": files,
        "materialization": materialization,
    }
    (output / "MODEL_SNAPSHOT_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2) + "\n"
    )
    metadata = {
        "title": "Qwen3 1.7B Base e249956c private snapshot",
        "id": dataset_id,
        "licenses": [{"name": "apache-2.0"}],
        "description": (
            "Private immutable snapshot of unsloth/Qwen3-1.7B-Base at revision "
            f"{revision}, retained for reproducible educational POC inference."
        ),
        "keywords": ["qwen3", "llm", "model-weights"],
    }
    (output / "dataset-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--expected-model-sha256", required=True)
    parser.add_argument("--dataset-id", required=True)
    args = parser.parse_args()
    manifest = build_snapshot(
        args.snapshot,
        args.output,
        revision=args.revision,
        expected_model_sha256=args.expected_model_sha256,
        dataset_id=args.dataset_id,
    )
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "revision": manifest["source"]["revision"],
                "model_sha256": manifest["model_sha256"],
                "files": len(manifest["files"]),
            }
        )
    )


if __name__ == "__main__":
    main()
