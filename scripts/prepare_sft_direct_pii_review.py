#!/usr/bin/env python3
"""Prepare a private direct-identifier review queue from contextual scan findings."""

import argparse
import json
from pathlib import Path

from triage_poc.privacy_audit import prepare_direct_identifier_review


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--findings", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare_direct_identifier_review(args.findings, args.output)))


if __name__ == "__main__":
    main()
