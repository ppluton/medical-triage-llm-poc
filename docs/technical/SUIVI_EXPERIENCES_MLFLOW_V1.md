# Suivi local des expériences avec MLflow

- Date : 2026-09-16
- Statut : implémenté, première ingestion distante en attente de la fin de v38
- Sources : documentation officielle MLflow Tracking API et stockage local

## Objectif

La commande `scripts/track_training_run.py` importe un run SFT ou DPO terminé dans un
store MLflow local sous `artifacts/`, donc hors Git. Elle relie paramètres, métriques,
manifeste de données et résumé du run sans copier les sorties médicales générées.

## Installation

```bash
python -m pip install -e '.[tracking]'
```

La version `mlflow==3.16.0` est épinglée. Le store est explicitement un URI `file://` local ;
aucun serveur, compte externe ou secret n'est nécessaire pour le POC.

## Exemple après récupération de v38

```bash
PYTHONPATH=src python scripts/track_training_run.py \
  --config configs/sft-v2.2-final-pilot.json \
  --summary artifacts/kaggle/v38/source-sft-v2-pilot/summary.json \
  --dataset-manifest data/manifests/derived-source-medical-qa-sft-v2.2-privacy-finalized.json \
  --stage-metric base=artifacts/kaggle/v38/source-sft-v2-pilot/base.json \
  --stage-metric pilot_end=artifacts/kaggle/v38/source-sft-v2-pilot/pilot_end.json \
  --tracking-directory artifacts/mlflow \
  --experiment-name chsa-medical-triage-poc \
  --run-name sft-v2.2-kaggle-v38
```

La commande refuse une divergence de checksum entre configuration, résumé et manifeste,
ainsi que tout run déclarant l'utilisation du test. Les rapports de génération restent hors
des artefacts MLflow ; seules leurs métriques agrégées sont importées.

## Limites

Le store local améliore la traçabilité et la reprise, mais ne constitue pas une sauvegarde
distante. Avant un usage d'équipe, il faudrait choisir un backend autorisé, définir ses accès,
sa rétention et son chiffrement. MLflow ne valide ni la qualité clinique ni la confidentialité
des artefacts qu'on lui donne : cette implémentation applique donc une liste minimale.
