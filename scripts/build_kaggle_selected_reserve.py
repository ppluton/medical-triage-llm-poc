#!/usr/bin/env python3
"""Package the one-shot selected-model reserve evaluation for private Kaggle."""

import argparse
import ast
import base64
import json
import lzma
from pathlib import Path

from triage_poc.comparison import sha256
from triage_poc.dpo import verify_completed_dpo
from triage_poc.final_reserve import validate_model_selection

BASE_DATASET_ID = "pierrepluton/qwen3-1-7b-base-e249956c"
SFT_DATASET_ID = "pierrepluton/chsa-sft-v39-step150-c911f9c6"
DPO_DATASET_ID = "pierrepluton/chsa-dpo-v41-policy-ae66169e-apache2"
RUN_NAME = "selected-triage-reserve-v1"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection", required=True, type=Path)
    parser.add_argument("--comparison-summary", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    decision = validate_model_selection(args.selection, args.comparison_summary)
    sft_manifest = root / "configs/sft-v39-handoff.json"
    sft_adapter = (
        root
        / "artifacts/kaggle/sft-v22-v40-reports/source-sft-v2-pilot/trainer/checkpoint-150"
    )
    dpo_run = root / "artifacts/kaggle/dpo-v41-reports/source-dpo-v41"
    dpo_proof = verify_completed_dpo(dpo_run, sft_manifest, sft_adapter)
    dpo_summary = dpo_run / "run_summary.json"

    names = [
        "scripts/run_selected_reserve.py",
        "configs/sft-v39-handoff.json",
        "data/manifests/synthetic-triage-held-out-reserve-v1.json",
        "data/samples/synthetic-triage-held-out-reserve-v1.json",
        "data/samples/synthetic-triage-development-v2.json",
    ]
    names += [
        f"src/triage_poc/{name}.py"
        for name in (
            "__init__",
            "api",
            "collection",
            "comparison",
            "dpo",
            "evaluation",
            "evaluation_reserve",
            "final_reserve",
            "model_snapshot",
            "sft_termination",
            "triage_probe",
            "triage_prompt",
            "ultramedical_audit",
        )
    ]
    files = {name: (root / name).read_text() for name in names}
    files["selection/model-selection.json"] = args.selection.read_text()
    files["selection/comparison-summary.json"] = args.comparison_summary.read_text()
    files["requirements.txt"] = (root / "requirements/dpo-kaggle.txt").read_text()
    for name, source_text in files.items():
        if not name.endswith(".py"):
            continue
        for node in ast.walk(ast.parse(source_text, filename=name)):
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module.startswith("triage_poc."):
                    required = "src/" + node.module.replace(".", "/") + ".py"
                    if required not in files:
                        raise ValueError(f"Missing bundled local import: {required}")

    encoded = base64.b85encode(lzma.compress(json.dumps(files).encode())).decode()
    bootstrap = (
        f"encoded={encoded!r}\n"
        f"sft_manifest_hash={sha256(sft_manifest)!r}\n"
        f"run_name={RUN_NAME!r}\n"
    )
    if decision["selected_variant"] == "dpo":
        bootstrap += (
            f"dpo_summary_hash={sha256(dpo_summary)!r}\n"
            f"dpo_adapter_hash={dpo_proof['adapter_sha256']!r}\n"
        )
    bootstrap += """from pathlib import Path
import base64, hashlib, json, lzma, os, shutil, subprocess, sys
root=Path('/kaggle/working/selected-reserve-code')
for name,text in json.loads(lzma.decompress(base64.b85decode(encoded))).items():
    path=root/name; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(text)
def locate(filename,digest):
    matches=[p for p in Path('/kaggle/input').rglob(filename)
        if hashlib.sha256(p.read_bytes()).hexdigest()==digest]
    if len(matches)!=1: raise ValueError('Expected one exact mounted artifact: '+filename)
    return matches[0]
sft_manifest=locate('SFT_HANDOFF_MANIFEST.json',sft_manifest_hash)
sft=sft_manifest.parent
subprocess.run([sys.executable,'-m','pip','install','-q','-r',str(root/'requirements.txt')],check=True)
subprocess.run([sys.executable,'-m','pip','uninstall','-y','torchao'],check=True)
command=[sys.executable,str(root/'scripts/run_selected_reserve.py'),
    '--selection',str(root/'selection/model-selection.json'),
    '--comparison-summary',str(root/'selection/comparison-summary.json'),
    '--sft-manifest',str(root/'configs/sft-v39-handoff.json'),
    '--sft-adapter',str(sft),
    '--reserve-manifest',str(root/'data/manifests/synthetic-triage-held-out-reserve-v1.json'),
    '--reserve',str(root/'data/samples/synthetic-triage-held-out-reserve-v1.json'),
    '--development-reference',str(root/'data/samples/synthetic-triage-development-v2.json'),
    '--output',str(Path('/kaggle/working')/run_name)]
if 'dpo_summary_hash' in globals():
    dpo_summary=locate('RUN_SUMMARY.json',dpo_summary_hash)
    dpo_weight=locate('adapter_model.safetensors',dpo_adapter_hash)
    if dpo_weight.parent.name!='policy': raise ValueError('Unexpected DPO policy layout')
    dpo=Path('/kaggle/working/selected-dpo-v41')
    shutil.copytree(dpo_weight.parent,dpo/'adapter/policy')
    shutil.copy2(dpo_summary,dpo/'run_summary.json')
    command.extend(['--dpo-run',str(dpo)])
subprocess.run(command,env=dict(os.environ,PYTHONPATH=str(root/'src'),
    PYTHONUNBUFFERED='1',CUDA_VISIBLE_DEVICES='0',TOKENIZERS_PARALLELISM='false'),
    check=True,timeout=3600)
"""
    compile(bootstrap, "selected-reserve-bootstrap", "exec")
    meta = json.loads(args.metadata.read_text())
    if (
        meta["id"] != "pierrepluton/chsa-source-sft-qwen3"
        or meta["is_private"] is not True
        or meta["machine_shape"] != "NvidiaTeslaT4"
    ):
        raise ValueError("Only the authorized private free T4 notebook may be used")
    meta["kernel_sources"] = []
    meta["dataset_sources"] = [BASE_DATASET_ID, SFT_DATASET_ID]
    if decision["selected_variant"] == "dpo":
        meta["dataset_sources"].append(DPO_DATASET_ID)
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
                    "# Réserve finale de triage — une seule variante sélectionnée\n"
                    "18 scénarios synthétiques gelés, zéro entraînement, "
                    "aucune validation clinique."
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
    notebook_path = args.output / meta["code_file"]
    notebook_path.write_text(json.dumps(notebook))
    (args.output / "kernel-metadata.json").write_text(json.dumps(meta, indent=2) + "\n")
    report = {
        "status": "prepared_for_authorized_one_shot_private_launch",
        "run_name": RUN_NAME,
        "selected_variant": decision["selected_variant"],
        "notebook_sha256": sha256(notebook_path),
        "optimizer_steps": 0,
        "reserve_records": 18,
        "selection_sha256": sha256(args.selection),
        "comparison_summary_sha256": sha256(args.comparison_summary),
        "sft_manifest_sha256": sha256(sft_manifest),
        "dpo_summary_sha256": sha256(dpo_summary),
        "dpo_adapter_sha256": dpo_proof["adapter_sha256"],
        "base_dataset_source": BASE_DATASET_ID,
        "sft_dataset_source": SFT_DATASET_ID,
        "dpo_dataset_source": (
            DPO_DATASET_ID if decision["selected_variant"] == "dpo" else None
        ),
        "clinical_validation": "not_performed",
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
