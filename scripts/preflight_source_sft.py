#!/usr/bin/env python3
"""Validate source SFT artifacts and measure tokenizer length before training."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from transformers import AutoTokenizer

from triage_poc.source_sft_preflight import (
    preflight_failures,
    rendered_token_summary,
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
    summaries = {split: rendered_token_summary(rows, tokenizer,
        max_sequence_length=args.max_sequence_length)
        for split, rows in [("train", train), ("validation", validation)]}
    failures = preflight_failures(summaries)
    result = {
        "status": "blocked" if failures else "passed",
        "failures": failures,
        "dataset_manifest_id": manifest["manifest_id"],
        "dataset_sha256": manifest["artifacts"]["canonical"]["sha256"],
        "model_path_name": args.model_path.name,
        "max_sequence_length": args.max_sequence_length,
        **summaries,
        "test_rendered_count": 0,
        "limits": [
            "Exact rendered text is checked; actual trainer labels require a runtime audit.",
            "This preflight proves data compatibility, not model quality or clinical safety.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": result["status"], "failures": failures,
                      "train": len(train), "validation": len(validation)}))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
