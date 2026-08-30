#!/usr/bin/env python3
"""Print a text-free audit of downloaded UltraMedical-Preference splits."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from triage_poc.ultramedical_audit import audit_ultramedical_preference


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("data_directory", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit_ultramedical_preference(args.data_directory), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
