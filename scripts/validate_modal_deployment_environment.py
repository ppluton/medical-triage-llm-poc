#!/usr/bin/env python3
"""Fail before a Modal deployment when required non-public inputs are absent."""

import argparse
import json

from triage_poc.modal_deployment import validate_deployment_environment


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predeploy", action="store_true")
    args = parser.parse_args()
    print(
        json.dumps(
            validate_deployment_environment(require_endpoint=not args.predeploy),
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
