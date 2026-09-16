# Préparation de la démonstration sans dépense

- Date : 2026-09-16
- Statut : `passed_local_contract_not_deployed`
- Révision : travail local postérieur à `46dba87`, à figer au prochain commit
- Environnement : macOS arm64, Python 3.13, aucun GPU ni endpoint extérieur lancé
- Sources : [ADR-019](../decisions/ADR-019-demonstration-zero-cout.md),
  [guide technique](../technical/DEMONSTRATION_KAGGLE_CLOUDFLARE_V1.md)

## Question

Le dépôt sait-il préparer, sans secret ni dépense, un notebook privé qui monte exactement la
Base et le SFT v39, refuse les identités divergentes et expose seulement l'API authentifiée à
travers un Quick Tunnel Cloudflare ?

## Commandes et résultats

Contrôle ciblé :

```bash
PYTHONPATH=.:src .venv/bin/pytest -q \
  tests/test_free_demo.py \
  tests/test_kaggle_free_demo_builder.py \
  tests/test_modal_deployment.py \
  tests/test_vllm_demo_guardrail_summary.py
```

Résultat : `14 passed`. Le builder a ensuite produit un notebook JSON valide dont les seules
sources de dataset sont :

- `pierrepluton/qwen3-1-7b-base-e249956c` ;
- `pierrepluton/chsa-sft-v39-step150-c911f9c6`.

Le notebook contient une cellule d'installation et une cellule interactive de service, reste
privé, demande une T4 et ne monte aucun DPO. Le token est lu depuis le secret Kaggle
`TRIAGE_API_TOKEN` sans être sérialisé dans le paquet.

Régression complète via `codex-validate` : Ruff passe, puis `245 passed` avec deux avertissements
de dépréciation Starlette/AnyIO déjà non bloquants. Job : `val_4c5c9d4f3132`, code 0.

## Ce que cela prouve

- Le contrat local du tunnel refuse un token court, une URL non TryCloudflare et un port
  invalide.
- Le notebook généré attache les deux couches exactes et exclut DPO/Modal.
- Le lanceur exige les checksums Base, SFT et `cloudflared` avant démarrage.
- La nouvelle brique ne régresse pas les 245 tests locaux du dépôt.

## Ce que cela ne prouve pas

Aucun notebook GPU n'a été lancé pendant cette validation. Il n'existe donc pas encore de
preuve de démarrage vLLM avec ce lanceur, d'URL `trycloudflare.com`, de smoke externe, de
latence distante, de persistance ou de CD. Quick Tunnel reste un outil de développement sans
SLA ; cette préparation n'est ni un déploiement permanent ni une validation clinique.
