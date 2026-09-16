#!/usr/bin/env python3
"""Log a completed training run to the local privacy-minimized MLflow store."""

import argparse
import json
from pathlib import Path

from triage_poc.experiment_tracking import build_tracking_payload, log_completed_run


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--summary", required=True, type=Path)
    parser.add_argument("--dataset-manifest", required=True, type=Path)
    parser.add_argument("--stage-metric", action="append", default=[])
    parser.add_argument("--tracking-directory", required=True, type=Path)
    parser.add_argument("--experiment-name", required=True)
    parser.add_argument("--run-name", required=True)
    args = parser.parse_args()
    stage_metrics = {}
    for value in args.stage_metric:
        stage, separator, path = value.partition("=")
        if not separator or not stage or stage in stage_metrics:
            raise ValueError("Stage metrics must be unique stage=/path/report.json values.")
        stage_metrics[stage] = Path(path)
    payload = build_tracking_payload(
        args.config, args.summary, args.dataset_manifest, stage_metrics
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
