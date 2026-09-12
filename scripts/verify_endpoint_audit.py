#!/usr/bin/env python3
"""Reconcile synthetic endpoint responses with private server audit evidence."""

import argparse
import json
from collections import Counter
from pathlib import Path

from triage_poc.comparison import sha256


def reconcile(report: dict, audit: list[dict]) -> dict:
    successful = [r for r in report["records"] if r.get("success") is True]
    expected = [r["response"]["interaction_id"] for r in successful]
    counts = Counter(expected)
    issues = []
    matched = 0
    for record in successful:
        identifier = record["response"]["interaction_id"]
        rows = [r for r in audit if r.get("interaction_id") == identifier]
        reasons = []
        if counts[identifier] != 1:
            reasons.append("duplicate_response_id")
        if len(rows) != 1:
            reasons.append("missing_or_duplicate_audit_entry")
        else:
            entry = rows[0]
            if entry.get("output") != record["response"]:
                reasons.append("response_audit_mismatch")
            if entry.get("privacy_status") != "passed" or not entry.get("anonymized_input"):
                reasons.append("missing_privacy_evidence")
            if not entry.get("prompt_version") or not entry.get("controls_version"):
                reasons.append("missing_version_evidence")
        if reasons:
            issues.append({"scenario_id": record["id"], "reasons": reasons})
        else:
            matched += 1
    return {
        "status": "passed" if successful and not issues else "failed",
        "successful_responses": len(successful), "matched_audit_entries": matched,
        "endpoint_failed_requests": len(report["records"]) - len(successful),
        "issues": issues,
        "limits": [
            "Checks the supplied audit export, not live storage durability or retention.",
            "Privacy status is recorded evidence, not independent anonymization validation.",
            "No clinical quality assertion; failed requests require separate investigation.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Fresh evidence path required")
    report = json.loads(args.report.read_text())
    audit = [json.loads(line) for line in args.audit.read_text().splitlines() if line.strip()]
    result = reconcile(report, audit)
    result.update(report_sha256=sha256(args.report), audit_sha256=sha256(args.audit))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in
                      ("status", "successful_responses", "matched_audit_entries")}))
    raise SystemExit(0 if result["status"] == "passed" else 1)


if __name__ == "__main__":
    main()
