#!/usr/bin/env python3
"""Build the private bounded Kaggle pilot with exact data reconstruction and GPU gates."""

# Preserve the already executed notebook source literals byte for byte.
# ruff: noqa: E501

import argparse
import base64
import hashlib
import json
import lzma
from pathlib import Path

BASE_DATASET_ID = "pierrepluton/qwen3-1-7b-base-e249956c"
BASE_MODEL_PATH = "/kaggle/input/qwen3-1-7b-base-e249956c"
BASE_MANIFEST_SHA256 = "920a5897431d1dfc62502815c5ec4929a149d5f324e6f5b2b3d86db4a691f0d1"

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--metadata", type=Path, required=True)
parser.add_argument("--report", type=Path, required=True)
parser.add_argument("--verify-pilot-summary", type=Path)
parser.add_argument("--memorization-manifest", type=Path)
parser.add_argument("--continue-pilot", action="store_true")
parser.add_argument("--config", type=Path, default=Path("configs/sft-v2.1-pilot.json"))
parser.add_argument(
    "--data-directory",
    type=Path,
    default=Path("data/processed/source-sft-v2.1-reviewed"),
)
args = parser.parse_args()
if args.continue_pilot and (args.memorization_manifest or args.verify_pilot_summary):
    parser.error("Continuation is separate from diagnostic and reload modes")
if args.memorization_manifest and args.verify_pilot_summary:
    parser.error("Choose memorization or reload, not both")
root = Path(__file__).resolve().parents[1]
config_path = args.config if args.config.is_absolute() else root / args.config
data_directory = (
    args.data_directory if args.data_directory.is_absolute() else root / args.data_directory
)
config_relative = str(config_path.relative_to(root))
out = args.output
out.mkdir(parents=True, exist_ok=False)
files = {
    f: (root / f).read_text()
    for f in [
        "scripts/run_source_sft_pilot.py",
        "src/triage_poc/__init__.py",
        "src/triage_poc/comparison.py",
        "src/triage_poc/model_snapshot.py",
        "src/triage_poc/sft_pilot.py",
        "src/triage_poc/sft_termination.py",
        config_relative,
    ]
}
if args.memorization_manifest:
    files["src/triage_poc/memorization.py"] = (root / "src/triage_poc/memorization.py").read_text()
    files["src/triage_poc/pilot_report.py"] = (root / "src/triage_poc/pilot_report.py").read_text()
    files["configs/sft-memorization-12.json"] = args.memorization_manifest.read_text()
if args.continue_pilot:
    for name in ("src/triage_poc/sft_continuation.py", "configs/sft-resume-150-to-500.json"):
        files[name] = (root / name).read_text()
payload = {}
expected = {}
system = None
for name in ("train-qwen3.jsonl", "validation-qwen3.jsonl"):
    p = data_directory / name
    rows = [json.loads(line) for line in p.read_text().splitlines()]
    system = rows[0]["messages"][0]["content"]
    assert all(r["messages"][0]["content"] == system for r in rows)
    payload[name] = [
        [r["record_id"], r["messages"][1]["content"], r["messages"][2]["content"]] for r in rows
    ]
    expected[name] = hashlib.sha256(p.read_bytes()).hexdigest()
encoded = base64.b85encode(
    lzma.compress(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode(), preset=9)
).decode()
# Verify exact byte reconstruction before upload, including sort order and newlines.
for name, rows in json.loads(lzma.decompress(base64.b85decode(encoded))).items():
    rebuilt = "".join(
        json.dumps(
            {
                "record_id": rid,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": q},
                    {"role": "assistant", "content": a},
                ],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n"
        for rid, q, a in rows
    ).encode()
    assert hashlib.sha256(rebuilt).hexdigest() == expected[name]
bootstrap = (
    """from pathlib import Path
import os, sys, json, lzma, base64, hashlib, subprocess
root=Path('/kaggle/working/pilot-code')
root.mkdir(parents=True)
"""
    + f"files={files!r}\n"
    + """for name,text in files.items():
    p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
"""
    + f"encoded={encoded!r}\nsystem={system!r}\nexpected={expected!r}\n"
    + f"config_relative={config_relative!r}\n"
    + """(root/'data').mkdir()
for name,rows in json.loads(lzma.decompress(base64.b85decode(encoded))).items():
    text=''.join(json.dumps({'record_id':rid,'messages':[{'role':'system','content':system},{'role':'user','content':q},{'role':'assistant','content':a}]},ensure_ascii=False,sort_keys=True)+'\\n' for rid,q,a in rows)
    p=root/'data'/name;p.write_text(text)
    assert hashlib.sha256(p.read_bytes()).hexdigest()==expected[name]
cfg=json.loads((root/config_relative).read_text())
candidates=[]
if cfg['base_model'].startswith('/kaggle/input/'):
    candidate=Path(cfg['base_model'])
    if all((candidate/n).is_file() and hashlib.sha256((candidate/n).read_bytes()).hexdigest()==h for n,h in cfg['tokenizer_files_sha256'].items()): candidates.append(candidate)
else:
    for p in Path('/kaggle/input').rglob('tokenizer.json'):
        if hashlib.sha256(p.read_bytes()).hexdigest()==cfg['tokenizer_files_sha256']['tokenizer.json']:
            if all((p.parent/n).is_file() and hashlib.sha256((p.parent/n).read_bytes()).hexdigest()==h for n,h in cfg['tokenizer_files_sha256'].items()): candidates.append(p.parent)
if not candidates: raise ValueError('No mounted tokenizer matches the audited files')
env=dict(os.environ,PYTHONPATH=str(root/'src'),PYTHONUNBUFFERED='1')
command=[sys.executable,str(root/'scripts/run_source_sft_pilot.py'),'--config',config_relative,'--data','data','--tokenizer',str(sorted(candidates,key=str)[0]),'--output','/kaggle/working/source-sft-v2-pilot']
subprocess.run(command,cwd=root,env=env,check=True)
smoke=command[:-1]+['/kaggle/working/fp16-smoke','--execute-pilot','--mechanics-smoke']
subprocess.run(smoke,cwd=root,env=env,check=True,timeout=900)
resume=command[:-1]+['/kaggle/working/fp16-resume','--execute-pilot','--mechanics-smoke','--resume-smoke-from','/kaggle/working/fp16-smoke/trainer/checkpoint-2']
subprocess.run(resume,cwd=root,env=env,check=True,timeout=900)
for name,steps in [('fp16-smoke',2),('fp16-resume',4)]:
    result=json.loads((Path('/kaggle/working')/name/'summary.json').read_text())
    assert result['status']=='mechanics_smoke_completed' and result['steps']==steps
print('GPU_SMOKE_AND_RESUME_PASSED_STARTING_BOUNDED_PILOT',flush=True)
subprocess.run(command+['--execute-pilot'],cwd=root,env=env,check=True,timeout=5400)
"""
)
if args.verify_pilot_summary:
    prior = json.loads(args.verify_pilot_summary.read_text())
    config = json.loads(files[config_relative])
    if prior.get("mode") != "pilot" or prior["configuration"] != config or prior["steps"] != 150:
        raise ValueError("Expected the completed frozen 150-step pilot")
    summary_hash = hashlib.sha256(args.verify_pilot_summary.read_bytes()).hexdigest()
    bootstrap = bootstrap.split("subprocess.run(command,cwd=root,env=env,check=True)")[0]
    bootstrap += f"expected_summary_hash={summary_hash!r}\n"
    bootstrap += """import shutil
matches=[p for p in Path('/kaggle/input').rglob('summary.json') if hashlib.sha256(p.read_bytes()).hexdigest()==expected_summary_hash]
if len(matches)!=1: raise ValueError('Expected exactly one pinned completed pilot input')
source=matches[0].parent
checkpoint=source/'trainer/checkpoint-150'
command[-1]='/kaggle/working/pilot-reload-verification'
# Preserve checkpoints even if the subsequent verification fails.
archive=Path('/kaggle/working/source-sft-v2-pilot')
shutil.copytree(source,archive)
subprocess.run(command+['--execute-pilot','--verify-pilot-from',str(checkpoint)],cwd=root,env=env,check=True,timeout=2700)
"""
if args.memorization_manifest:
    bootstrap = bootstrap.split("subprocess.run(command,cwd=root,env=env,check=True)")[0]
    bootstrap += """import shutil
matches=[p for p in Path('/kaggle/input').rglob('source-sft-v2-pilot/summary.json') if hashlib.sha256(p.read_bytes()).hexdigest()=='099979378a042473ec910194bec48d54ed02a6fba206c97d0558c04f5da447c9']
if len(matches)!=1: raise ValueError('Expected one preserved pilot archive')
shutil.copytree(matches[0].parent,Path('/kaggle/working/source-sft-v2-pilot'))
command[-1]='/kaggle/working/train-memorization-12'
command+=['--memorization-manifest','configs/sft-memorization-12.json']
subprocess.run(command,cwd=root,env=env,check=True)
subprocess.run(command+['--execute-pilot'],cwd=root,env=env,check=True,timeout=2400)
"""
if args.continue_pilot:
    bootstrap = bootstrap.split("subprocess.run(command,cwd=root,env=env,check=True)")[0]
    bootstrap += """import shutil
plan=json.loads((root/'configs/sft-resume-150-to-500.json').read_text())
matches=[p for p in Path('/kaggle/input').rglob('source-sft-v2-pilot/summary.json') if hashlib.sha256(p.read_bytes()).hexdigest()==plan['source_summary_sha256']]
if len(matches)!=1: raise ValueError('Expected exactly one verified general pilot')
source=matches[0].parent
shutil.copytree(source,Path('/kaggle/working/source-sft-v2-pilot'))
command[-1]='/kaggle/working/source-sft-v2-continuation-500'
command+=['--continue-pilot-from',str(source/'trainer/checkpoint-150'),'--continuation-plan','configs/sft-resume-150-to-500.json']
subprocess.run(command,cwd=root,env=env,check=True)
subprocess.run(command+['--execute-pilot'],cwd=root,env=env,check=True,timeout=5400)
shutil.copy2(source/'base.json',Path('/kaggle/working/source-sft-v2-continuation-500/base.json'))
"""
install = {
    "cell_type": "code",
    "metadata": {},
    "source": [
        '%pip install -q --retries 10 --timeout 30 "unsloth==2026.8.22" "unsloth_zoo==2026.8.16" "datasets==4.3.0" "transformers==5.5.0" "trl==0.23.1" "peft==0.18.1" "accelerate==1.14.0" "bitsandbytes==0.50.2" "pyyaml==6.0.3"\n',
        "%pip uninstall -y torchao",
    ],
    "execution_count": None,
    "outputs": [],
}
uses_local_base = json.loads(files[config_relative])["base_model"] == BASE_MODEL_PATH
base_preflight = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": (
        "import hashlib,json\n"
        "from pathlib import Path\n"
        f"base=Path({BASE_MODEL_PATH!r})\n"
        "manifest=base/'MODEL_SNAPSHOT_MANIFEST.json'\n"
        "digest=lambda p: hashlib.sha256(p.read_bytes()).hexdigest()\n"
        f"assert digest(manifest)=={BASE_MANIFEST_SHA256!r}\n"
        "payload=json.loads(manifest.read_text())\n"
        "for name,info in payload['files'].items():\n"
        " p=base/name\n"
        " assert p.is_file() and p.stat().st_size==info['size'] and "
        "digest(p)==info['sha256'],name\n"
        "print('BASE_SNAPSHOT_PREFLIGHT_PASSED',len(payload['files']))\n"
    ).splitlines(keepends=True),
}
notebook_metadata = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}
}
nb = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": notebook_metadata,
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# Pilote SFT v2 depuis la base\n150 étapes ou 30 minutes de phase entraînement. 3721 train, 479 validation, aucun test. Notebook privé, T4 gratuite."
            ],
        },
        *([base_preflight] if uses_local_base else []),
        install,
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": bootstrap.splitlines(keepends=True),
        },
    ],
}
if args.verify_pilot_summary:
    nb["cells"][0]["source"] = [
        "# Vérification du pilote sauvegardé\nRecharge finale puis comparaison des checkpoints 50/100/150 sur 479 références et 30 générations par checkpoint. Zéro étape d’entraînement."
    ]
if args.memorization_manifest:
    nb["cells"][0]["source"] = [
        "# Diagnostic de mémorisation sur 12 exemples train\n300 étapes ou 900 secondes d’entraînement. Aucun score de généralisation, aucun SFT complet."
    ]
if args.continue_pilot:
    nb["cells"][0]["source"] = [
        "# Reprise SFT générale 150 vers 500\nMême corpus et scheduler, 350 nouvelles étapes au maximum ou 1800 secondes de phase entraînement. Vérification de recharge avant optimisation. Aucun poids du diagnostic de mémorisation."
    ]
p = out / "chsa-source-sft-qwen3.ipynb"
p.write_text(json.dumps(nb, ensure_ascii=False))
assert p.stat().st_size < 1_000_000, p.stat().st_size
meta = json.loads(args.metadata.read_text())
if (
    meta["id"] != "pierrepluton/chsa-source-sft-qwen3"
    or meta["is_private"] is not True
    or meta["machine_shape"] != "NvidiaTeslaT4"
):
    raise ValueError("Builder restricted to the authorized private T4 notebook")
if args.verify_pilot_summary or args.memorization_manifest or args.continue_pilot:
    meta["kernel_sources"] = ["pierrepluton/chsa-source-sft-qwen3"]
if uses_local_base:
    sources = list(meta.get("dataset_sources", []))
    if BASE_DATASET_ID not in sources:
        sources.append(BASE_DATASET_ID)
    meta["dataset_sources"] = sources
    if not (args.verify_pilot_summary or args.memorization_manifest or args.continue_pilot):
        meta["kernel_sources"] = []
(out / "kernel-metadata.json").write_text(json.dumps(meta, indent=2) + "\n")
report = {
    "status": "prepared_for_authorized_private_launch",
    "notebook_bytes": p.stat().st_size,
    "notebook_sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
    "files_sha256": {k: hashlib.sha256(v.encode()).hexdigest() for k, v in files.items()},
    "data_sha256": expected,
    "codec": "lzma_base85_compact_rows_exact_reconstruction_verified",
    "test_records_used": 0,
    "kernel": meta["id"],
    "private": meta["is_private"],
    "gpu": meta["machine_shape"],
}
if args.verify_pilot_summary:
    report["mode"] = "read_only_pilot_reload"
    report["source_pilot_summary_sha256"] = summary_hash
    report["optimizer_steps_to_execute"] = 0
if args.memorization_manifest:
    report["mode"] = "train_only_memorization"
    report["manifest_sha256"] = hashlib.sha256(args.memorization_manifest.read_bytes()).hexdigest()
    report["optimizer_steps_cap"] = 300
if args.continue_pilot:
    report["mode"] = "general_pilot_continuation"
    report["start_step"] = 150
    report["stop_step"] = 500
    report["new_steps_cap"] = 350
    report["training_seconds_cap"] = 1800
args.report.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
