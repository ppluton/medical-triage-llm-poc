#!/usr/bin/env python3
"""Audit a pinned local MedQuAD checkout without emitting source text."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from triage_poc.medquad_audit import audit_medquad


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = audit_medquad(args.repository)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    totals = report["totals"]
    print(
        "MedQuAD candidate audit completed: "
        f"xml={totals['xml_files']}, qa_pairs={totals['qa_pairs']}, "
        f"nonempty_answers={totals['nonempty_answers']}, "
        f"empty_answers={totals['empty_answers']}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
