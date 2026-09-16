#!/usr/bin/env python3
"""Package the v39-bound DPO run for the authorized private free T4 notebook."""

import argparse
import base64
import json
import lzma
from pathlib import Path

from triage_poc.comparison import sha256
from triage_poc.dpo import load_dpo_handoff, load_sft_identity

SOURCE_SUMMARY_SHA256 = "41a7e0c8e54154bac44f4bb6a21e3fe5a5b80a97523409b86a359f1f7b7972b2"
RUN_NAME = "source-dpo-v41"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    source = root / "artifacts/kaggle/sft-v22-v40-reports/source-sft-v2-pilot"
    adapter = source / "trainer/checkpoint-150"
    identity_path = root / "configs/sft-v39-handoff.json"
    comparison = root / "docs/evidence/SFT_V39_DPO_COMPARISON_2026-09-16.json"
    decision = root / "docs/evidence/DPO_V39_EXPERIMENT_DECISION_2026-09-16.json"
    dataset = root / "artifacts/dpo-reviewed-v3-v22-bound"
    identity = load_sft_identity(identity_path, adapter)
    load_dpo_handoff(
        dataset,
        comparison,
        decision,
        sft_sha256=identity["files"]["adapter_model.safetensors"],
    )
    if sha256(source / "summary.json") != SOURCE_SUMMARY_SHA256:
        raise ValueError("Selected v39 SFT summary changed.")
    if decision.is_file():
        decision_data = json.loads(decision.read_text())
        if (
            decision_data.get("sft_handoff_sha256") != sha256(identity_path)
            or decision_data.get("dpo_dataset_manifest_sha256")
            != sha256(dataset / "manifest.json")
            or decision_data.get("max_optimizer_steps") != 20
        ):
            raise ValueError("DPO decision does not match selected SFT, dataset, or budget.")

    fixed_files = {
        "configs/selected-sft-handoff.json": identity_path,
        "docs/evidence/selected-sft-comparison.json": comparison,
        "docs/evidence/selected-dpo-decision.json": decision,
        "requirements/dpo-kaggle.txt": root / "requirements/dpo-kaggle.txt",
        "scripts/run_dpo.py": root / "scripts/run_dpo.py",
    }
    for name in ("__init__", "comparison", "dpo", "ultramedical_audit"):
        fixed_files[f"src/triage_poc/{name}.py"] = root / f"src/triage_poc/{name}.py"
    files = {name: path.read_text() for name, path in fixed_files.items()}
    files.update(
        {
            f"data/{name}": (dataset / name).read_text()
            for name in ("manifest.json", "train.jsonl", "validation.jsonl")
        }
    )
    encoded = base64.b85encode(lzma.compress(json.dumps(files).encode())).decode()
    bootstrap = f"encoded={encoded!r}\nsource_hash={SOURCE_SUMMARY_SHA256!r}\n"
    bootstrap += f"run_name={RUN_NAME!r}\n"
    bootstrap += """from pathlib import Path
import base64, hashlib, json, lzma, os, subprocess, sys
root=Path('/kaggle/working/dpo-code')
for name,text in json.loads(lzma.decompress(base64.b85decode(encoded))).items():
    path=root/name; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(text)
matches=[p for p in Path('/kaggle/input').rglob('source-sft-v2-pilot/summary.json')
    if hashlib.sha256(p.read_bytes()).hexdigest()==source_hash]
if len(matches)!=1: raise ValueError('Expected one exact verified v39 SFT archive')
source=matches[0].parent
adapter=source/'trainer/checkpoint-150'
subprocess.run([sys.executable,'-m','pip','install','-q','-r',str(root/'requirements/dpo-kaggle.txt')],check=True)
subprocess.run([sys.executable,'-m','pip','uninstall','-y','torchao'],check=True)
command=[sys.executable,str(root/'scripts/run_dpo.py'),
    '--sft-manifest',str(root/'configs/selected-sft-handoff.json'),
    '--sft-adapter',str(adapter),
    '--comparison',str(root/'docs/evidence/selected-sft-comparison.json'),
    '--decision',str(root/'docs/evidence/selected-dpo-decision.json'),
    '--dataset',str(root/'data'),'--max-steps','20',
    '--output',str(Path('/kaggle/working')/run_name)]
subprocess.run(command,env=dict(os.environ,PYTHONPATH=str(root/'src'),
    PYTHONUNBUFFERED='1',CUDA_VISIBLE_DEVICES='0',TOKENIZERS_PARALLELISM='false'),
    check=True,timeout=5400)
"""
    compile(bootstrap, "dpo-v39-bootstrap", "exec")
    meta = json.loads(args.metadata.read_text())
    if (
        meta["id"] != "pierrepluton/chsa-source-sft-qwen3"
        or meta["is_private"] is not True
        or meta["machine_shape"] != "NvidiaTeslaT4"
    ):
        raise ValueError("Only the authorized private free T4 notebook may be used.")
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
                    "# DPO pédagogique v39 - 20 étapes\n426 train / 54 validation, "
                    "préférences sources anglaises, aucune validation clinique, "
                    "réserve finale fermée."
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
        "mode": "bounded_educational_dpo",
        "run_name": RUN_NAME,
        "notebook_sha256": sha256(notebook_path),
        "source_sft_summary_sha256": SOURCE_SUMMARY_SHA256,
        "sft_handoff_sha256": sha256(identity_path),
        "sft_adapter_sha256": identity["files"]["adapter_model.safetensors"],
        "dataset_manifest_sha256": sha256(dataset / "manifest.json"),
        "comparison_sha256": sha256(comparison),
        "decision_sha256": sha256(decision),
        "optimizer_steps_cap": 20,
        "test_records_used": 0,
        "held_out_triage_reserve_used": False,
        "private": True,
        "gpu": "NvidiaTeslaT4",
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
