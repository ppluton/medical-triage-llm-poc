#!/usr/bin/env python3
"""Log a verified DPO run to the privacy-minimized local MLflow store."""

import argparse
import json
from pathlib import Path

from triage_poc.experiment_tracking import build_dpo_tracking_payload, log_completed_run


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "summary",
        "trainer-state",
        "dataset-manifest",
        "sft-manifest",
        "verification",
        "tracking-directory",
    ):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--experiment-name", required=True)
    parser.add_argument("--run-name", required=True)
    args = parser.parse_args()
    payload = build_dpo_tracking_payload(
        args.summary,
        args.trainer_state,
        args.dataset_manifest,
        args.sft_manifest,
        args.verification,
    )
    print(
        json.dumps(
            log_completed_run(
                payload,
                args.tracking_directory,
                experiment_name=args.experiment_name,
                run_name=args.run_name,
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
