#!/usr/bin/env python3
"""Build the private interactive Kaggle notebook for the zero-cost demonstration."""

from __future__ import annotations

import argparse
import base64
import json
import lzma
from pathlib import Path

BASE_DATASET_ID = "pierrepluton/qwen3-1-7b-base-e249956c"
SFT_DATASET_ID = "pierrepluton/chsa-sft-v39-step150-c911f9c6"
BASE_MODEL_PATH = "/kaggle/input/qwen3-1-7b-base-e249956c"
SFT_MANIFEST_SHA256 = "5a8ffc133b42b5cb7b72ec75daed1190e8701286203e9d03c8de15d010004da5"
CLOUDFLARED_VERSION = "2026.9.1"
CLOUDFLARED_SHA256 = "03f1f25d1cc93b9ad6c60569d44060bc4f17ed97075760ed8cfca4b12dcd68cc"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    metadata = json.loads(args.metadata.read_text())
    if (
        metadata["id"] != "pierrepluton/chsa-source-sft-qwen3"
        or metadata["is_private"] is not True
        or metadata["machine_shape"] != "NvidiaTeslaT4"
    ):
        raise ValueError("Authorized private T4 notebook required")

    names = [
        "scripts/run_free_kaggle_cloudflare_demo.py",
        "requirements/api.txt",
    ]
    names += [str(path.relative_to(root)) for path in (root / "src/triage_poc").glob("*.py")]
    payload = {name: (root / name).read_text() for name in names}
    encoded = base64.b85encode(lzma.compress(json.dumps(payload).encode())).decode()

    setup = f"""encoded={encoded!r}
import base64, hashlib, json, lzma, os, stat, subprocess, sys, urllib.request
from pathlib import Path
root=Path('/kaggle/working/free-demo-code')
for name,text in json.loads(lzma.decompress(base64.b85decode(encoded))).items():
    path=root/name; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(text)
def digest(path):
    value=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8*1024*1024),b''): value.update(chunk)
    return value.hexdigest()
matches=[path for path in Path('/kaggle/input').rglob('SFT_HANDOFF_MANIFEST.json')
    if digest(path)=={SFT_MANIFEST_SHA256!r}]
if len(matches)!=1: raise ValueError('Expected one exact SFT v39 manifest')
sft=matches[0].parent
base_model=Path({BASE_MODEL_PATH!r})
subprocess.run([sys.executable,'-m','pip','install','-q','virtualenv==20.35.4'],check=True,timeout=180)
for name in ('vllm','api'):
    subprocess.run([sys.executable,'-m','virtualenv','/tmp/chsa-'+name],check=True,timeout=120)
vpy='/tmp/chsa-vllm/bin/python'; apy='/tmp/chsa-api/bin/python'
subprocess.run([vpy,'-m','pip','install','--no-cache-dir','vllm==0.15.0'],check=True,timeout=1800)
subprocess.run([apy,'-m','pip','install','--no-cache-dir','-r',str(root/'requirements/api.txt')],check=True,timeout=900)
subprocess.run([apy,'-m','pip','install','--no-cache-dir','--no-deps',
 'https://github.com/explosion/spacy-models/releases/download/fr_core_news_md-3.8.0/fr_core_news_md-3.8.0-py3-none-any.whl',
 'https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl'],check=True,timeout=600)
cloudflared=Path('/kaggle/working/cloudflared')
urllib.request.urlretrieve(
    'https://github.com/cloudflare/cloudflared/releases/download/{CLOUDFLARED_VERSION}/cloudflared-linux-amd64',
    cloudflared)
if digest(cloudflared)!={CLOUDFLARED_SHA256!r}: raise ValueError('cloudflared checksum mismatch')
cloudflared.chmod(stat.S_IRUSR|stat.S_IWUSR|stat.S_IXUSR)
print(json.dumps({{'status':'setup_ready','base_model':str(base_model),'adapter':str(sft),
    'cloudflared_sha256':digest(cloudflared)}},indent=2))
"""
    serve = """from kaggle_secrets import UserSecretsClient
os.environ['TRIAGE_API_TOKEN']=UserSecretsClient().get_secret('TRIAGE_API_TOKEN')
command=[sys.executable,str(root/'scripts/run_free_kaggle_cloudflare_demo.py'),
    '--vllm-python',vpy,'--api-python',apy,'--cloudflared',str(cloudflared),
    '--base-model',str(base_model),'--adapter',str(sft),
    '--output','/kaggle/working/chsa-free-demo']
environment=dict(os.environ,PYTHONPATH=str(root/'src'),PYTHONUNBUFFERED='1')
subprocess.run(command+['--preflight'],env=environment,check=True,timeout=180)
subprocess.run(command,env=environment,check=True,timeout=43200)
"""
    compile(setup, "free-demo-setup", "exec")
    compile(serve, "free-demo-serve", "exec")

    metadata["kernel_sources"] = []
    metadata["dataset_sources"] = [BASE_DATASET_ID, SFT_DATASET_ID]
    notebook = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"}
        },
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# Démonstration CHSA sans dépense\n",
                    "Notebook privé interactif : SFT v39 + vLLM + API + Quick Tunnel. "
                    "Scénarios synthétiques uniquement.\n",
                ],
            },
            {
                "cell_type": "code",
                "metadata": {},
                "execution_count": None,
                "outputs": [],
                "source": setup.splitlines(keepends=True),
            },
            {
                "cell_type": "code",
                "metadata": {},
                "execution_count": None,
                "outputs": [],
                "source": serve.splitlines(keepends=True),
            },
        ],
    }
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / metadata["code_file"]).write_text(json.dumps(notebook))
    (args.output / "kernel-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")


if __name__ == "__main__":
    main()
