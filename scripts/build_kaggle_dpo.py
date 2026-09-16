#!/usr/bin/env python3
"""Package the reviewed DPO experiment for the authorized private free T4 notebook."""

import argparse
import base64
import json
import lzma
from pathlib import Path

from triage_poc.comparison import sha256
from triage_poc.dpo import load_dpo_handoff, load_sft_identity


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    source = root / "artifacts/kaggle/continuation-v22-reports/source-sft-v2-continuation-500"
    identity_path = root / "configs/sft-v22-handoff.json"
    comparison = root / "docs/evidence/SFT_V22_DPO_COMPARISON_2026-09-12.json"
    decision = root / "docs/evidence/DPO_EXPERIMENT_DECISION_2026-09-12.json"
    dataset = root / "artifacts/dpo-reviewed-v1"
    identity = load_sft_identity(identity_path, source / "trainer/checkpoint-500")
    load_dpo_handoff(dataset, comparison, decision,
                     sft_sha256=identity["files"]["adapter_model.safetensors"])
    names = ["scripts/run_dpo.py", "configs/sft-v22-handoff.json",
             "docs/evidence/SFT_V22_DPO_COMPARISON_2026-09-12.json",
             "docs/evidence/DPO_EXPERIMENT_DECISION_2026-09-12.json",
             "requirements/dpo-kaggle.txt"]
    names += [f"src/triage_poc/{name}.py" for name in
              ("__init__", "comparison", "dpo", "ultramedical_audit")]
    files = {name: (root / name).read_text() for name in names}
    files.update({f"data/{name}": (dataset / name).read_text()
                  for name in ("manifest.json", "train.jsonl", "validation.jsonl")})
    encoded = base64.b85encode(lzma.compress(json.dumps(files).encode())).decode()
    bootstrap = f"encoded={encoded!r}\nsource_hash={sha256(source / 'summary.json')!r}\n"
    bootstrap += '''from pathlib import Path
import base64, hashlib, json, lzma, os, shutil, subprocess, sys
root=Path('/kaggle/working/dpo-code')
for name,text in json.loads(lzma.decompress(base64.b85decode(encoded))).items():
    path=root/name; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(text)
matches=[p for p in Path('/kaggle/input').rglob('summary.json')
    if hashlib.sha256(p.read_bytes()).hexdigest()==source_hash]
if len(matches)!=1: raise ValueError('Expected one exact v22 SFT archive')
source=matches[0].parent
shutil.copytree(source,Path('/kaggle/working/source-sft-v2-continuation-500'))
subprocess.run([sys.executable,'-m','pip','install','-q','-r',str(root/'requirements/dpo-kaggle.txt')],check=True)
subprocess.run([sys.executable,'-m','pip','uninstall','-y','torchao'],check=True)
command=[sys.executable,str(root/'scripts/run_dpo.py'),
    '--sft-manifest',str(root/'configs/sft-v22-handoff.json'),
    '--sft-adapter',str(source/'trainer/checkpoint-500'),
    '--comparison',str(root/'docs/evidence/SFT_V22_DPO_COMPARISON_2026-09-12.json'),
    '--decision',str(root/'docs/evidence/DPO_EXPERIMENT_DECISION_2026-09-12.json'),
    '--dataset',str(root/'data'),'--max-steps','20',
    '--output','/kaggle/working/source-dpo-v27']
subprocess.run(command,env=dict(os.environ,PYTHONPATH=str(root/'src'),
    PYTHONUNBUFFERED='1',CUDA_VISIBLE_DEVICES='0',TOKENIZERS_PARALLELISM='false'),
    check=True,timeout=5400)
'''
    compile(bootstrap, "dpo-bootstrap", "exec")
    meta = json.loads(args.metadata.read_text())
    if (meta["id"] != "pierrepluton/chsa-source-sft-qwen3"
            or meta["is_private"] is not True or meta["machine_shape"] != "NvidiaTeslaT4"):
        raise ValueError("Only the authorized private free T4 notebook may be used")
    meta["kernel_sources"] = [meta["id"]]
    notebook = {"nbformat": 4, "nbformat_minor": 5,
                "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python",
                                             "name": "python3"}},
                "cells": [{"cell_type": "markdown", "metadata": {}, "source": [
                    "# DPO pédagogique — 20 étapes\n426 train / 54 validation, "
                    "préférences sources filtrées, aucune validation clinique. "
                    "SFT général 500 comme politique et référence ; test final inutilisé."]},
                    {"cell_type": "code", "metadata": {}, "execution_count": None,
                     "outputs": [], "source": bootstrap.splitlines(keepends=True)}]}
    args.output.mkdir(parents=True, exist_ok=False)
    path = args.output / meta["code_file"]
    path.write_text(json.dumps(notebook))
    (args.output / "kernel-metadata.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps({"notebook_sha256": sha256(path), "bytes": path.stat().st_size,
                      "optimizer_steps": 20,
                      "dataset_manifest_sha256": sha256(dataset / "manifest.json")}))


if __name__ == "__main__":
    main()
