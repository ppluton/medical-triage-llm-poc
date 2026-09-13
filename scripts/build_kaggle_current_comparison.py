#!/usr/bin/env python3
"""Package identical Base/SFT/DPO evaluation using the completed private notebook output."""

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
    sft_summary = (
        root
        / "artifacts/kaggle/continuation-v22-reports/source-sft-v2-continuation-500/summary.json"
    )
    dpo_summary = root / "artifacts/kaggle/dpo-v27-metrics/source-dpo-v27/run_summary.json"
    summary = json.loads(dpo_summary.read_text())
    if (
        summary["status"] != "completed_educational_dpo"
        or summary["test_records_used"] != 0
        or summary["weight_checks"]["reference_unchanged"] is not True
    ):
        raise ValueError("Completed DPO with unchanged reference required")
    names = [
        "scripts/run_current_comparison.py",
        "configs/sft-v22-handoff.json",
        "data/manifests/derived-source-medical-qa-sft-v2.1-reviewed.json",
        "data/processed/source-sft-v2.1-reviewed/validation-qwen3.jsonl",
        "data/samples/synthetic-triage-development-v2.json",
    ]
    names += [
        f"src/triage_poc/{name}.py"
        for name in (
            "__init__",
            "api",
            "comparison",
            "dpo",
            "evaluation",
            "sft_termination",
            "triage_probe",
            "triage_prompt",
            "ultramedical_audit",
        )
    ]
    files = {name: (root / name).read_text() for name in names}
    files["requirements.txt"] = (
        root / "requirements/dpo-kaggle.txt"
    ).read_text() + "fastapi==0.141.1\n"
    encoded = base64.b85encode(lzma.compress(json.dumps(files).encode())).decode()
    bootstrap = (
        f"encoded={encoded!r}\nsft_hash={sha256(sft_summary)!r}\ndpo_hash={sha256(dpo_summary)!r}\n"
    )
    bootstrap += """from pathlib import Path
import base64, hashlib, json, lzma, os, shutil, subprocess, sys
root=Path('/kaggle/working/current-comparison-code')
for name,text in json.loads(lzma.decompress(base64.b85decode(encoded))).items():
    path=root/name; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(text)
def locate(filename,digest):
    matches=[p for p in Path('/kaggle/input').rglob(filename)
        if hashlib.sha256(p.read_bytes()).hexdigest()==digest]
    if len(matches)!=1: raise ValueError('Expected one exact archive: '+filename)
    return matches[0].parent
sft=locate('summary.json',sft_hash)
dpo=locate('run_summary.json',dpo_hash)
shutil.copytree(sft,Path('/kaggle/working/source-sft-v2-continuation-500'))
shutil.copytree(dpo,Path('/kaggle/working/source-dpo-v27'))
subprocess.run([sys.executable,'-m','pip','install','-q','-r',str(root/'requirements.txt')],check=True)
subprocess.run([sys.executable,'-m','pip','uninstall','-y','torchao'],check=True)
command=[sys.executable,str(root/'scripts/run_current_comparison.py'),
    '--sft-manifest',str(root/'configs/sft-v22-handoff.json'),
    '--sft-adapter',str(sft/'trainer/checkpoint-500'),'--dpo-run',str(dpo),
    '--data-manifest',str(root/'data/manifests/derived-source-medical-qa-sft-v2.1-reviewed.json'),
    '--validation',str(root/'data/processed/source-sft-v2.1-reviewed/validation-qwen3.jsonl'),
    '--prior-qa',str(sft/'pilot_end.json'),
    '--scenarios',str(root/'data/samples/synthetic-triage-development-v2.json'),
    '--output','/kaggle/working/current-comparison-v28']
subprocess.run(command,env=dict(os.environ,PYTHONPATH=str(root/'src'),
    PYTHONUNBUFFERED='1',CUDA_VISIBLE_DEVICES='0',TOKENIZERS_PARALLELISM='false'),
    check=True,timeout=7200)
"""
    compile(bootstrap, "comparison-bootstrap", "exec")
    meta = json.loads(args.metadata.read_text())
    if (
        meta["id"] != "pierrepluton/chsa-source-sft-qwen3"
        or meta["is_private"] is not True
        or meta["machine_shape"] != "NvidiaTeslaT4"
    ):
        raise ValueError("Only the authorized private free T4 notebook may be used")
    meta["kernel_sources"] = [meta["id"]]
    notebook = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}
        },
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# Comparaison Base / SFT / DPO\n479 validations QA, 30 générations QA, "
                    "18 scénarios synthétiques de triage. Même runtime et paramètres. "
                    "Zéro entraînement, test final inutilisé, pas de validation clinique."
                ],
            },
            {
                "cell_type": "code",
                "metadata": {},
                "execution_count": None,
                "outputs": [],
                "source": bootstrap.splitlines(keepends=True),
            },
        ],
    }
    args.output.mkdir(parents=True, exist_ok=False)
    path = args.output / meta["code_file"]
    path.write_text(json.dumps(notebook))
    (args.output / "kernel-metadata.json").write_text(json.dumps(meta, indent=2))
    print(
        json.dumps(
            {
                "notebook_sha256": sha256(path),
                "bytes": path.stat().st_size,
                "optimizer_steps": 0,
                "sft_run_sha256": sha256(sft_summary),
                "dpo_run_sha256": sha256(dpo_summary),
            }
        )
    )


if __name__ == "__main__":
    main()
