#!/usr/bin/env python3
"""Package a private loopback vLLM/API measurement using existing saved adapters."""

import argparse
import base64
import json
import lzma
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    meta = json.loads(args.metadata.read_text())
    if (
        meta["id"] != "pierrepluton/chsa-source-sft-qwen3"
        or meta["is_private"] is not True
        or meta["machine_shape"] != "NvidiaTeslaT4"
    ):
        raise ValueError("Authorized private T4 notebook required")
    names = [
        "scripts/run_vllm_api_demo.py",
        "scripts/evaluate_triage_endpoint.py",
        "scripts/verify_endpoint_audit.py",
        "requirements/api.txt",
        "data/samples/synthetic-triage-development-v2.json",
    ]
    names += [str(p.relative_to(root)) for p in (root / "src/triage_poc").glob("*.py")]
    encoded = base64.b85encode(
        lzma.compress(json.dumps({name: (root / name).read_text() for name in names}).encode())
    ).decode()
    code = (
        f"encoded={encoded!r}\n"
        + """import base64, hashlib, json, lzma, os, shutil, subprocess, sys
from pathlib import Path
root=Path('/kaggle/working/vllm-demo-code')
for name,text in json.loads(lzma.decompress(base64.b85decode(encoded))).items():
    path=root/name; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(text)
def locate(filename,digest):
    matches=[p for p in Path('/kaggle/input').rglob(filename)
        if hashlib.sha256(p.read_bytes()).hexdigest()==digest]
    if len(matches)!=1: raise ValueError('Expected exactly one saved archive')
    return matches[0].parent
sft=locate('summary.json','45d6c88ef5e17e150a38f5ca7593212619ff854febe10901635f98913a6edb75')
dpo=locate('run_summary.json','dd65fa9a7612bc76ca46cd102353ca5b853fe1545569338ed7b42fb7f39a970a')
shutil.copytree(sft,Path('/kaggle/working/source-sft-v2-continuation-500'))
shutil.copytree(dpo,Path('/kaggle/working/source-dpo-v27'))
subprocess.run([sys.executable,'-m','pip','install','-q','virtualenv==20.35.4'],check=True,timeout=180)
for name in ('vllm','api'):
    subprocess.run([sys.executable,'-m','virtualenv','/tmp/chsa-'+name],check=True,timeout=120)
vpy='/tmp/chsa-vllm/bin/python'; apy='/tmp/chsa-api/bin/python'
subprocess.run([vpy,'-m','pip','install','--no-cache-dir','vllm==0.15.0'],check=True,timeout=1800)
subprocess.run([apy,'-m','pip','install','--no-cache-dir','-r',str(root/'requirements/api.txt')],check=True,timeout=900)
subprocess.run([apy,'-m','pip','install','--no-cache-dir','--no-deps',
 'https://github.com/explosion/spacy-models/releases/download/fr_core_news_md-3.8.0/fr_core_news_md-3.8.0-py3-none-any.whl',
 'https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl'],check=True,timeout=600)
for name,python in (('vllm',vpy),('api',apy)):
    with (root/(name+'-packages.txt')).open('w') as out:
        subprocess.run([python,'-m','pip','freeze'],stdout=out,check=True)
subprocess.run([sys.executable,str(root/'scripts/run_vllm_api_demo.py'),
 '--vllm-python',vpy,'--api-python',apy,'--sft',str(sft/'trainer/checkpoint-500'),
 '--dpo',str(dpo/'adapter/policy'),'--scenarios',str(root/'data/samples/synthetic-triage-development-v2.json'),
 '--output','/kaggle/working/vllm-api-v30'],check=True,timeout=4800)
"""
    )
    compile(code, "vllm-demo-bootstrap", "exec")
    meta["kernel_sources"] = [meta["id"]]
    notebook = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"}
        },
        "cells": [
            {
                "id": "vllm-api-demo",
                "cell_type": "code",
                "metadata": {},
                "execution_count": None,
                "outputs": [],
                "source": code.splitlines(keepends=True),
            }
        ],
    }
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / meta["code_file"]).write_text(json.dumps(notebook))
    (args.output / "kernel-metadata.json").write_text(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
