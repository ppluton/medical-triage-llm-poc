#!/usr/bin/env python3
"""Validate source SFT artifacts and measure tokenizer length before training."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from transformers import AutoTokenizer

from triage_poc.source_sft_preflight import (
    token_length_summary,
    validate_source_sft_artifacts,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--artifact-directory", required=True, type=Path)
    parser.add_argument("--model-path", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--max-sequence-length", type=int, default=2048)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.max_sequence_length <= 0:
        raise ValueError("--max-sequence-length must be positive.")
    if not args.model_path.is_dir():
        raise FileNotFoundError(f"Model snapshot not found: {args.model_path}.")
    manifest, _, train, validation = validate_source_sft_artifacts(
        args.manifest, args.artifact_directory
    )
    tokenizer = AutoTokenizer.from_pretrained(str(args.model_path), local_files_only=True)
    result = {
        "status": "passed",
        "dataset_manifest_id": manifest["manifest_id"],
        "dataset_sha256": manifest["artifacts"]["canonical"]["sha256"],
        "model_path_name": args.model_path.name,
        "max_sequence_length": args.max_sequence_length,
        "train": token_length_summary(
            train, tokenizer, max_sequence_length=args.max_sequence_length
        ),
        "validation": token_length_summary(
            validation, tokenizer, max_sequence_length=args.max_sequence_length
        ),
        "test_rendered_count": 0,
        "limits": [
            "Token lengths are a content proxy; exact Qwen3 chat-template overhead is measured "
            "by the trainer runtime.",
            "This preflight proves data compatibility, not model quality or clinical safety.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        "Source SFT preflight passed: "
        f"train={len(train)}, validation={len(validation)}, test_rendered=0, "
        f"train_p95={result['train']['p95']} tokens."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
