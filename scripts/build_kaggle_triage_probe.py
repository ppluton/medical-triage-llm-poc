#!/usr/bin/env python3
"""Package the read-only triage comparison for the existing private T4 notebook."""

import argparse
import base64
import json
import lzma
from pathlib import Path

from triage_poc.comparison import sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    source = root / "artifacts/kaggle/continuation-v22-reports/source-sft-v2-continuation-500"
    prior = json.loads((source / "pilot_end.json").read_text())
    wanted = {r["record_id"] for r in prior["records"]}
    validation = [
        json.loads(line)
        for line in (root / "data/processed/source-sft-v2.1-reviewed/validation-qwen3.jsonl")
        .read_text()
        .splitlines()
    ]
    selected = [r for r in validation if r["record_id"] in wanted]
    if len(selected) != len(wanted):
        raise ValueError("Missing reload comparison records")
    names = [
        "scripts/run_triage_probe.py",
        "configs/sft-v22-handoff.json",
        "data/samples/synthetic-triage-development-v2.json",
    ]
    names += [
        f"src/triage_poc/{n}.py"
        for n in (
            "__init__",
            "api",
            "evaluation",
            "triage_probe",
            "triage_prompt",
            "comparison",
            "dpo",
            "ultramedical_audit",
        )
    ]
    files = {name: (root / name).read_text() for name in names}
    files["data/qa-validation.jsonl"] = "".join(json.dumps(r) + "\n" for r in selected)
    encoded = base64.b85encode(lzma.compress(json.dumps(files).encode())).decode()
    bootstrap = f"encoded={encoded!r}\nsource_hash={sha256(source / 'summary.json')!r}\n"
    bootstrap += """from pathlib import Path
import base64, hashlib, json, lzma, os, shutil, subprocess, sys
root=Path('/kaggle/working/triage-probe-code')
for name,text in json.loads(lzma.decompress(base64.b85decode(encoded))).items():
    path=root/name; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(text)
matches=[p for p in Path('/kaggle/input').rglob('summary.json')
    if hashlib.sha256(p.read_bytes()).hexdigest()==source_hash]
if len(matches)!=1: raise ValueError('Expected one exact v22 completed run')
source=matches[0].parent
shutil.copytree(source,Path('/kaggle/working/source-sft-v2-continuation-500'))
command=[sys.executable,str(root/'scripts/run_triage_probe.py'),
    '--sft-manifest',str(root/'configs/sft-v22-handoff.json'),
    '--checkpoint',str(source/'trainer/checkpoint-500'),
    '--scenarios',str(root/'data/samples/synthetic-triage-development-v2.json'),
    '--prior-qa',str(source/'pilot_end.json'),
    '--qa-validation',str(root/'data/qa-validation.jsonl'),
    '--output','/kaggle/working/triage-base-sft-v25']
subprocess.run(command,env=dict(os.environ,PYTHONPATH=str(root/'src'),PYTHONUNBUFFERED='1'),check=True,timeout=5400)
"""
    meta = json.loads(args.metadata.read_text())
    if (
        meta["id"] != "pierrepluton/chsa-source-sft-qwen3"
        or meta["is_private"] is not True
        or meta["machine_shape"] != "NvidiaTeslaT4"
    ):
        raise ValueError("Only the authorized private free T4 notebook may be used")
    meta["kernel_sources"] = [meta["id"]]
    install = (
        '%pip install -q "unsloth==2026.8.22" "unsloth_zoo==2026.8.16" '
        '"datasets==4.3.0" "transformers==5.5.0" "trl==0.23.1" "peft==0.18.1" '
        '"accelerate==1.14.0" "bitsandbytes==0.50.2" "fastapi==0.141.1" '
        '"ijson==3.5.1"\n%pip uninstall -y torchao'
    )
    cells = [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# Comparaison de triage Base/SFT\n18 scénarios synthétiques FR/EN, "
                "références proposées ; recharge SFT vérifiée sur 30 QA. Zéro entraînement."
            ],
        }
    ]
    for code in (install, bootstrap):
        cells.append(
            {
                "cell_type": "code",
                "metadata": {},
                "execution_count": None,
                "outputs": [],
                "source": code.splitlines(keepends=True),
            }
        )
    notebook = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}
        },
        "cells": cells,
    }
    args.output.mkdir(parents=True, exist_ok=False)
    path = args.output / meta["code_file"]
    path.write_text(json.dumps(notebook))
    if path.stat().st_size >= 1_000_000:
        raise ValueError("Notebook exceeds upload budget")
    (args.output / "kernel-metadata.json").write_text(json.dumps(meta, indent=2))
    print(
        json.dumps(
            {
                "notebook_sha256": sha256(path),
                "bytes": path.stat().st_size,
                "optimizer_steps": 0,
                "source_run_sha256": sha256(source / "summary.json"),
            }
        )
    )


if __name__ == "__main__":
    main()
