#!/usr/bin/env python3
"""Run a deterministic, text-free Presidio audit of MEDIQA questions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from triage_poc.anonymization import TextAnonymizer
from triage_poc.mediqa_audit import audit_presidio_question_sample


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("repository", type=Path)
    parser.add_argument("--sample-per-file", type=int, default=10)
    args = parser.parse_args()
    anonymizer = TextAnonymizer()
    report = audit_presidio_question_sample(
        args.repository,
        anonymizer,
        sample_per_file=args.sample_per_file,
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
