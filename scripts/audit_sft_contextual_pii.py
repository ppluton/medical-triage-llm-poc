#!/usr/bin/env python3
"""Scan a canonical SFT corpus for contextual PII candidates without rewriting it."""

import argparse
import json
from importlib import metadata
from pathlib import Path

from triage_poc.anonymization import build_presidio_analyzer
from triage_poc.privacy_audit import audit_contextual_pii


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    summary = audit_contextual_pii(
        args.canonical,
        args.output,
        analyzer=build_presidio_analyzer(),
    )
    summary["presidio_analyzer_version"] = metadata.version("presidio-analyzer")
    (args.output / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    )
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
