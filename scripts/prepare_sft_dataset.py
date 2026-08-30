#!/usr/bin/env python3
"""Create an Unsloth-compatible JSONL file from canonical synthetic SFT records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from triage_poc.sft_dataset import (
    SftDatasetError,
    render_qwen3_text_dataset,
    render_sft_dataset,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", type=Path, required=True, help="Canonical JSON array of SFT records"
    )
    parser.add_argument(
        "--output", type=Path, required=True, help="Generated JSONL output outside Git"
    )
    parser.add_argument(
        "--split",
        choices=("train", "validation"),
        help="Prepare only one canonical split; keep test records excluded.",
    )
    parser.add_argument(
        "--format",
        choices=("messages", "qwen3-text"),
        default="messages",
        help="Output structured messages or text pre-rendered with Unsloth's qwen3 template.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    records = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise SftDatasetError("The input file must contain a JSON array.")
    if args.split:
        records = [record for record in records if record.get("split") == args.split]
        if not records:
            raise SftDatasetError(f"No SFT records found for split '{args.split}'.")
    rendered = (
        render_qwen3_text_dataset(records)
        if args.format == "qwen3-text"
        else render_sft_dataset(records)
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as output_file:
        for record in rendered:
            output_file.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"Prepared {len(rendered)} SFT conversations at {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
