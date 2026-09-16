#!/usr/bin/env python3
"""Create a DPO-ready SFT identity from verified run and reload artifacts."""

import argparse
import json
from pathlib import Path

from triage_poc.sft_handoff import build_sft_handoff


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--reload", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--dataset-manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--checkpoint-label", required=True)
    args = parser.parse_args()
    result = build_sft_handoff(
        args.run,
        args.reload,
        args.config,
        args.dataset_manifest,
        args.output,
        checkpoint_label=args.checkpoint_label,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
