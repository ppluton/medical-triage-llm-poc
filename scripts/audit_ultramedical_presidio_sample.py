#!/usr/bin/env python3
"""Run a deterministic Presidio sample audit on preference triples."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from triage_poc.anonymization import TextAnonymizer
from triage_poc.ultramedical_audit import audit_presidio_preference_sample


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("data_directory", type=Path)
    parser.add_argument("--sample-per-split", type=int, default=10)
    args = parser.parse_args()
    report = audit_presidio_preference_sample(
        args.data_directory,
        TextAnonymizer(),
        sample_per_split=args.sample_per_split,
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
