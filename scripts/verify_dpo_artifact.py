#!/usr/bin/env python3
"""Verify a completed DPO artifact before admitting it to model comparisons."""

import argparse
import json
from pathlib import Path

from triage_poc.dpo import verify_completed_dpo


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("run", "sft-manifest", "sft-adapter", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Fresh evidence path required")
    result = verify_completed_dpo(args.run, args.sft_manifest, args.sft_adapter)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
