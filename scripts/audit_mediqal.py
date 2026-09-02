#!/usr/bin/env python3
"""Print a text-free inventory report for a pinned MediQAl checkout."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from triage_poc.mediqal_audit import audit_mediqal


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit_mediqal(args.repository), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
