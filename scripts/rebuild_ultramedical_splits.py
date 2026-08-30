#!/usr/bin/env python3
"""Build a text-free UltraMedical-Preference split decision index."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from triage_poc.ultramedical_rebuild import rebuild_ultramedical_splits


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("data_directory", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    report = rebuild_ultramedical_splits(args.data_directory, args.output)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
