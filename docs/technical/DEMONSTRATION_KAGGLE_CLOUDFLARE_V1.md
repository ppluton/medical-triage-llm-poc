# Démonstration Kaggle + Cloudflare sans dépense

- Date : 2026-09-16
- Statut : `implemented_locally_not_executed_remotely`
- Sources : [ADR-019](../decisions/ADR-019-demonstration-zero-cout.md),
  [résultat vLLM v37](../evidence/VLLM_V37_RESULT_2026-09-16.md),
  [Quick Tunnels](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/)

## Périmètre

Le lanceur `scripts/run_free_kaggle_cloudflare_demo.py` conserve la chaîne déjà éprouvée sur
Kaggle : Base figée, SFT v39, vLLM 0.15.0 et factory FastAPI. Il ajoute uniquement une URL
HTTPS temporaire Cloudflare. Il ne réentraîne rien et ne modifie pas les preuves du run v37.

Le lanceur échoue avant démarrage si :

- le token applicatif contient moins de 32 caractères ;
- le snapshot Base ou l'adaptateur ne correspond pas aux checksums attendus ;
- le binaire `cloudflared` n'est pas celui épinglé ;
- vLLM ne publie pas `chsa-selected` ;
- `/healthz` échoue localement ou à travers le tunnel.

## Construction du notebook privé

Le builder attache uniquement les deux ressources privées checksum-lockées (Base et SFT v39)
et crée deux cellules : installation bornée, puis préflight et service interactif. Il produit
un notebook privé distinct, `pierrepluton/chsa-free-demo-qwen3`, afin de ne jamais écraser le
notebook historique `pierrepluton/chsa-source-sft-qwen3` ni ses versions de preuve.

```bash
.venv/bin/python scripts/build_kaggle_free_demo.py \
  --metadata artifacts/kaggle/api-guardrails-v37/kernel-metadata.json \
  --output /chemin/prive/kaggle-free-demo

kaggle kernels push -p /chemin/prive/kaggle-free-demo
```

Le notebook généré n'est pas destiné à une exécution planifiée permanente : la seconde
cellule reste active tant que la démonstration est servie.

## Installation bornée dans le notebook privé

Le runtime vLLM/API reprend la procédure de
[préparation vLLM](VLLM_DEMONSTRATION_V1.md). Télécharger ensuite le binaire Linux AMD64
officiel épinglé et contrôler son empreinte avant de le rendre exécutable :

```bash
CLOUDFLARED_VERSION=2026.9.1
curl -fsSLo /kaggle/working/cloudflared \
  "https://github.com/cloudflare/cloudflared/releases/download/${CLOUDFLARED_VERSION}/cloudflared-linux-amd64"
echo "03f1f25d1cc93b9ad6c60569d44060bc4f17ed97075760ed8cfca4b12dcd68cc  /kaggle/working/cloudflared" \
  | sha256sum --check --strict
chmod 700 /kaggle/working/cloudflared
```

Créer un secret Kaggle nommé `TRIAGE_API_TOKEN`, aléatoire et d'au moins 32 caractères. Le
charger sans l'afficher :

```python
import os
from kaggle_secrets import UserSecretsClient

os.environ["TRIAGE_API_TOKEN"] = UserSecretsClient().get_secret("TRIAGE_API_TOKEN")
```

## Préflight puis service

Les chemins Base et adaptateur doivent pointer vers les ressources privées déjà attachées.
Exécuter d'abord le préflight :

```bash
PYTHONPATH=/kaggle/working/vllm-demo-code/src \
python /kaggle/working/vllm-demo-code/scripts/run_free_kaggle_cloudflare_demo.py \
  --vllm-python /tmp/chsa-vllm/bin/python \
  --api-python /tmp/chsa-api/bin/python \
  --cloudflared /kaggle/working/cloudflared \
  --base-model /kaggle/input/qwen3-1-7b-base-e249956c \
  --adapter /chemin/prive/sft-v39/trainer/checkpoint-500 \
  --output /kaggle/working/chsa-free-demo \
  --preflight
```

Retirer `--preflight` pour démarrer la démonstration. Le processus affiche et écrit l'URL
dans `chsa-free-demo/endpoint.json`, mais n'écrit jamais le token. Depuis le poste de
démonstration :

```bash
TRIAGE_API_TOKEN='valeur-conservee-hors-git' \
python scripts/evaluate_triage_endpoint.py \
  --url 'https://sous-domaine-aleatoire.trycloudflare.com' \
  --scenarios data/samples/modal-smoke-scenarios.json \
  --output /chemin/prive/free-demo-smoke.json
```

Un `Ctrl-C`, l'arrêt du notebook ou l'expiration de la session arrête vLLM, FastAPI et le
tunnel. Télécharger ensuite `endpoint.json`, `audit.jsonl` et le smoke privé si une preuve de
session est nécessaire. Ne pas versionner les logs bruts avant revue des données.

## Ce que cette brique prouve et ne prouve pas

Une exécution distante réussie prouvera qu'un client extérieur peut joindre temporairement
la chaîne authentifiée et checksum-lockée. Le code et ses tests locaux seuls ne le prouvent
pas. Même exécutée, cette démonstration ne prouvera ni SLA, ni persistance, ni CI/CD GPU, ni
sûreté clinique, ni aptitude à recevoir des données réelles.
