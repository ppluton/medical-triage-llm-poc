#!/usr/bin/env python3
"""Export reserved QA with the shared renderer and preserve its source manifest."""

import argparse
import json
from pathlib import Path

from triage_poc.comparison import sha256, validate_conversations
from triage_poc.source_sft import render_source_test_conversation


def export_test(canonical: Path, source_manifest: Path, output: Path) -> dict:
    if output.exists():
        raise ValueError("Fresh export directory required")
    manifest = json.loads(source_manifest.read_text())
    entry = manifest["artifacts"]["canonical"]
    if sha256(canonical) != entry["sha256"]:
        raise ValueError("Canonical checksum mismatch")
    records = [json.loads(line) for line in canonical.read_text().splitlines()]
    if len(records) != entry["record_count"]:
        raise ValueError("Canonical population mismatch")
    identifiers = [record["record_id"] for record in records]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("Duplicate canonical identifiers")
    test = [
        render_source_test_conversation(record) for record in records if record["split"] == "test"
    ]
    if len(test) != 500:
        raise ValueError("Exactly 500 reserved examples required")
    validate_conversations(test)
    output.mkdir(parents=True)
    target = output / "test-qwen3.jsonl"
    target.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in test)
    )
    manifest["artifacts"]["test_qwen3"] = {
        "path": target.name,
        "record_count": len(test),
        "sha256": sha256(target),
        "byte_size": target.stat().st_size,
    }
    manifest["parent_manifest_sha256"] = sha256(source_manifest)
    manifest["status"] = "reserved_test_export_not_evaluated"
    manifest["test_export_code_sha256"] = {
        "exporter": sha256(Path(__file__)),
        "renderer": sha256(Path(__file__).resolve().parents[1] / "src/triage_poc/source_sft.py"),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return {"status": manifest["status"], "record_count": len(test), "sha256": sha256(target)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("canonical", "source-manifest", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(export_test(args.canonical, args.source_manifest, args.output)))


if __name__ == "__main__":
    main()
