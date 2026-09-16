#!/usr/bin/env python3
"""Package the matched Base/SFT-v39/DPO-v41 development comparison."""

import argparse
import ast
import base64
import json
import lzma
from pathlib import Path

from triage_poc.comparison import sha256
from triage_poc.dpo import verify_completed_dpo

SFT_DATASET_ID = "pierrepluton/chsa-sft-v39-step150-c911f9c6"
BASE_DATASET_ID = "pierrepluton/qwen3-1-7b-base-e249956c"
RUN_NAME = "current-comparison-v43"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    sft_manifest = root / "configs/sft-v39-handoff.json"
    sft_adapter = (
        root
        / "artifacts/kaggle/sft-v22-v40-reports/source-sft-v2-pilot/trainer/checkpoint-150"
    )
    dpo = root / "artifacts/kaggle/dpo-v41-reports/source-dpo-v41"
    dpo_proof = verify_completed_dpo(dpo, sft_manifest, sft_adapter)
    dpo_summary = dpo / "run_summary.json"
    prior = json.loads(
        (
            root / "artifacts/kaggle/sft-v22-v40-reports/source-sft-v2-pilot/pilot_end.json"
        ).read_text()
    )
    prior_ids = [row["record_id"] for row in prior["records"]]
    if len(prior_ids) != 30 or len(set(prior_ids)) != 30:
        raise ValueError("Expected thirty unique frozen SFT generation IDs.")
    names = [
        "scripts/run_current_comparison.py",
        "configs/sft-v39-handoff.json",
        "data/manifests/derived-source-medical-qa-sft-v2.2-privacy-finalized.json",
        "data/processed/source-sft-v2.2-privacy-finalized/validation-qwen3.jsonl",
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
            "final_selection",
            "sft_termination",
            "triage_probe",
            "triage_prompt",
            "ultramedical_audit",
        )
    ]
    files = {name: (root / name).read_text() for name in names}
    files["data/prior-qa-ids.json"] = json.dumps(
        {"records": [{"record_id": identifier} for identifier in prior_ids]}, indent=2
    )
    files["requirements.txt"] = (
        (root / "requirements/dpo-kaggle.txt").read_text() + "fastapi==0.141.1\n"
    )
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
        f"dpo_hash={sha256(dpo_summary)!r}\n"
        f"run_name={RUN_NAME!r}\n"
    )
    bootstrap += """from pathlib import Path
import base64, hashlib, json, lzma, os, subprocess, sys
root=Path('/kaggle/working/current-comparison-code')
for name,text in json.loads(lzma.decompress(base64.b85decode(encoded))).items():
    path=root/name; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(text)
def locate(filename,digest):
    matches=[p for p in Path('/kaggle/input').rglob(filename)
        if hashlib.sha256(p.read_bytes()).hexdigest()==digest]
    if len(matches)!=1: raise ValueError('Expected one exact mounted artifact: '+filename)
    return matches[0]
sft_manifest=locate('SFT_HANDOFF_MANIFEST.json',sft_manifest_hash)
sft=sft_manifest.parent
dpo_summary=locate('run_summary.json',dpo_hash)
dpo=dpo_summary.parent
subprocess.run([sys.executable,'-m','pip','install','-q','-r',str(root/'requirements.txt')],check=True)
subprocess.run([sys.executable,'-m','pip','uninstall','-y','torchao'],check=True)
command=[sys.executable,str(root/'scripts/run_current_comparison.py'),
    '--sft-manifest',str(root/'configs/sft-v39-handoff.json'),
    '--sft-adapter',str(sft),'--dpo-run',str(dpo),
    '--data-manifest',str(root/'data/manifests/derived-source-medical-qa-sft-v2.2-privacy-finalized.json'),
    '--validation',str(root/'data/processed/source-sft-v2.2-privacy-finalized/validation-qwen3.jsonl'),
    '--prior-qa',str(root/'data/prior-qa-ids.json'),
    '--scenarios',str(root/'data/samples/synthetic-triage-development-v2.json'),
    '--output',str(Path('/kaggle/working')/run_name)]
subprocess.run(command,env=dict(os.environ,PYTHONPATH=str(root/'src'),
    PYTHONUNBUFFERED='1',CUDA_VISIBLE_DEVICES='0',TOKENIZERS_PARALLELISM='false'),
    check=True,timeout=7200)
"""
    compile(bootstrap, "comparison-v42-bootstrap", "exec")
    meta = json.loads(args.metadata.read_text())
    if (
        meta["id"] != "pierrepluton/chsa-source-sft-qwen3"
        or meta["is_private"] is not True
        or meta["machine_shape"] != "NvidiaTeslaT4"
    ):
        raise ValueError("Only the authorized private free T4 notebook may be used.")
    meta["kernel_sources"] = [meta["id"]]
    meta["dataset_sources"] = [BASE_DATASET_ID, SFT_DATASET_ID]
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
                    "# Comparaison Base / SFT v39 / DPO v41\n479 validations QA, "
                    "30 générations QA et 18 scénarios synthétiques de développement. "
                    "Zéro entraînement, aucun test final, aucune validation clinique."
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
        "status": "prepared_for_authorized_private_launch",
        "run_name": RUN_NAME,
        "notebook_sha256": sha256(notebook_path),
        "optimizer_steps": 0,
        "sft_manifest_sha256": sha256(sft_manifest),
        "sft_adapter_sha256": json.loads(sft_manifest.read_text())["files"][
            "adapter_model.safetensors"
        ],
        "dpo_run_sha256": sha256(dpo_summary),
        "dpo_adapter_sha256": dpo_proof["adapter_sha256"],
        "validation_records": 479,
        "qa_generation_records": 30,
        "synthetic_development_records": 18,
        "test_records_used": 0,
        "held_out_triage_reserve_used": False,
        "sft_dataset_source": SFT_DATASET_ID,
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
