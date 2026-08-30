#!/usr/bin/env python3
"""Print a text-free inventory report for a local MEDIQA 2019 checkout."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from triage_poc.mediqa_audit import audit_mediqa


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("repository", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit_mediqa(args.repository), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
