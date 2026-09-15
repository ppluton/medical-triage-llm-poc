#!/usr/bin/env python3
"""Build the privacy-finalized source SFT v2.2 candidate."""

import argparse
import json
from pathlib import Path

from triage_poc.privacy_finalize import finalize_sft_privacy


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical", required=True, type=Path)
    parser.add_argument("--findings", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--manifest-output", required=True, type=Path)
    parser.add_argument("--canonical-sha256", required=True)
    parser.add_argument("--findings-sha256", required=True)
    parser.add_argument("--code-revision", required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    if args.manifest_output.exists():
        raise ValueError("Choose a fresh manifest output path.")
    manifest = finalize_sft_privacy(
        args.canonical,
        args.findings,
        args.output,
        expected_canonical_sha256=args.canonical_sha256,
        expected_findings_sha256=args.findings_sha256,
        code_revision=args.code_revision,
        run_id=args.run_id,
    )
    args.manifest_output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "record_count": manifest["record_count"],
                "split_counts": manifest["split_counts"],
                "privacy_review": manifest["privacy_review"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
