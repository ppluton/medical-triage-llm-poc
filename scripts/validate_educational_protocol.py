#!/usr/bin/env python3
"""Validate the educational-only protocol and print a text-free summary."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from triage_poc.educational_protocol import load_educational_protocol


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--schema", required=True, type=Path)
    args = parser.parse_args()

    protocol = load_educational_protocol(args.protocol, args.schema)
    summary = {
        "protocol_id": protocol["protocol_id"],
        "status": protocol["status"],
        "clinical_validation_performed": protocol["clinical_validation"]["performed"],
        "dataset_plan": protocol["dataset_plan"],
        "risk_family_count": len(protocol["risk_families"]),
        "sha256": hashlib.sha256(args.protocol.read_bytes()).hexdigest(),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
