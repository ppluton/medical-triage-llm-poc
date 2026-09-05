#!/usr/bin/env python3
"""Build a self-contained private Kaggle comparison notebook, without patient/test text."""
import argparse
import json
from pathlib import Path

from triage_poc.source_sft_preflight import validate_source_sft_artifacts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--include-synthetic-probe", action="store_true")
    parser.add_argument("--count", type=int, default=500)
    parser.add_argument("--generate-count", type=int, default=30)
    parser.add_argument("--stop-on-message-end", action="store_true")
    parser.add_argument("--precision", choices=["4bit-default", "4bit-nf4", "float16"],
                        default="4bit-default")
    args = parser.parse_args()
    if not 0 <= args.generate_count <= args.count <= 500 or args.count == 0:
        parser.error("Require 0 <= generate-count <= count <= 500 and count > 0")
    root = Path(__file__).resolve().parents[1]
    _, canonical, _, _ = validate_source_sft_artifacts(
        root / "data/manifests/derived-source-medical-qa-sft-v1.json", args.artifacts)
    metadata = {r["record_id"]: {"source": r["source"]["source_dataset"],
                                "language": r["language"], "split": "validation"}
                for r in canonical if r["split"] == "validation"}
    files = {p: (root / p).read_text() for p in [
        "src/triage_poc/__init__.py", "src/triage_poc/comparison.py",
        "scripts/run_model_comparison.py"]}
    files["validation-metadata.json"] = json.dumps(metadata)
    if args.include_synthetic_probe:
        files["scenario-protocol.json"] = (
            root / "configs/synthetic-schema-probe-v1.json").read_text()
    setup = '''%pip install -q "transformers==5.5.0" "peft==0.18.1" "accelerate==1.14.0"
%pip install -q "bitsandbytes==0.50.2"
%pip uninstall -y torchao
'''
    materialize = "import os\nimport subprocess\nimport sys\nfrom pathlib import Path\n\n"
    materialize += "root = Path('/kaggle/working/comparison-code')\n"
    materialize += "files = " + repr(files) + "  # noqa: E501 - embedded source payload\n"
    materialize += """for name, content in files.items():
    target = root / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
"""
    run = '''import hashlib
import zipfile

# Use mounted inputs only; the CLI does not reliably pin a notebook source version.
sft_output = Path('/kaggle/input')
adapters = list(sft_output.rglob('adapter_config.json'))
if not adapters:
    archives = list(sft_output.rglob('source-sft-cuda-full.zip'))
    if len(archives) != 1:
        raise ValueError('Attach the archived SFT v5 adapter or its original ZIP first')
    archive = archives[0]
    destination = Path('/kaggle/working/archived-sft-v5')
    with zipfile.ZipFile(archive) as z:
        for member in z.infolist():
            if not (destination / member.filename).resolve().is_relative_to(destination.resolve()):
                raise ValueError('Unsafe archive path')
        z.extractall(destination)
    adapters = list(destination.rglob('best-adapter/adapter_config.json'))
# Kaggle can mount the same output through multiple paths. Select only verified weights.
expected = '3f050ae77a4b66ecf4a254a407a463a046143437198ac5dfbd7922b75b28a940'
verified = []
for config in adapters:
    weights = config.parent / 'adapter_model.safetensors'
    with weights.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() == expected:
            verified.append(config)
if not verified:
    raise ValueError('No adapter matches the archived SFT checksum')
adapters = sorted(verified, key=lambda p: (len(str(p)), str(p)))
validation = [p for p in Path('/kaggle/input').rglob('validation.jsonl')
              if p.stat().st_size == 580691]
if len(validation) != 1:
    raise ValueError('Expected one private source-SFT validation artifact')
env = dict(os.environ, PYTHONPATH=str(root / 'src'))
command = [sys.executable, str(root / 'scripts/run_model_comparison.py'),
           '--validation', str(validation[0]), '--metadata', str(root / 'validation-metadata.json'),
           '--sft-adapter', str(adapters[0].parent),
           '--output', '/kaggle/working/base-sft-comparison-v1']
subprocess.run(command + ['--dry-run'], env=env, check=True)
subprocess.run(command, env=env, check=True)
'''
    runtime_args = ["--count", str(args.count), "--generate-count", str(args.generate_count),
                    "--precision", args.precision]
    if args.stop_on_message_end:
        runtime_args.append("--stop-on-message-end")
    run = run.replace("subprocess.run(command +",
                      f"command += {runtime_args!r}\nsubprocess.run(command +")
    if args.include_synthetic_probe:
        run = run.replace("subprocess.run(command +",
            "command += ['--scenario-protocol', str(root / 'scenario-protocol.json')]\n"
            "subprocess.run(command +")
    cells = [{"cell_type": "markdown", "metadata": {}, "source": [
        "# Comparaison Base / SFT — validation de développement\n",
        "Notebook privé, quota gratuit. SFT v5 conservé. Aucun entraînement ni test final.\n",
        f"Les {args.count} références QA mesurent la vraisemblance ; "
        f"{args.generate_count} sorties par modèle sont à revoir. "
        "Aucune validation clinique.\n"]}]
    for source in [setup, materialize, run]:
        cells.append({"cell_type": "code", "metadata": {}, "execution_count": None,
                      "outputs": [], "source": source.splitlines(keepends=True)})
    for number, cell in enumerate(cells):
        cell["id"] = f"comparison-{number}"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"nbformat": 4, "nbformat_minor": 5,
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python",
                                    "name": "python3"}}, "cells": cells}, indent=1) + "\n")


if __name__ == "__main__":
    main()
