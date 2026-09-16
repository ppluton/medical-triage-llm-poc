#!/usr/bin/env python3
"""Freeze and checksum the synthetic held-out triage reserve."""

import argparse
import json
from pathlib import Path

from triage_poc.evaluation_reserve import freeze_triage_reserve


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reserve", required=True, type=Path)
    parser.add_argument("--development", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Choose a fresh manifest output path.")
    manifest = freeze_triage_reserve(args.reserve, args.development)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": manifest["status"], **manifest["counts"]}))


if __name__ == "__main__":
    main()
