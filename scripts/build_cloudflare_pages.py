#!/usr/bin/env python3
"""Build the static Cloudflare Pages directory without embedding configuration or secrets."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEMO_SOURCE = REPOSITORY_ROOT / "src" / "triage_poc" / "demo_ui"
PAGES_STATIC = REPOSITORY_ROOT / "deploy" / "cloudflare_pages" / "static"
DEFAULT_OUTPUT = REPOSITORY_ROOT / "deploy" / "cloudflare_pages" / "dist"


def build(output: Path) -> None:
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    for source in (DEMO_SOURCE, PAGES_STATIC):
        shutil.copytree(source, output, dirs_exist_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    build(args.output.resolve())


if __name__ == "__main__":
    main()
