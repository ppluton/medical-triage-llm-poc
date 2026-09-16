# Suivi local des expériences avec MLflow

- Date : 2026-09-16
- Statut : implémenté, première ingestion v39 vérifiée
- Sources : documentation officielle MLflow Tracking API et stockage local

## Objectif

La commande `scripts/track_training_run.py` importe un run SFT ou DPO terminé dans un
store MLflow SQLite local sous `artifacts/`, donc hors Git. Elle relie paramètres, métriques,
manifeste de données et résumé du run sans copier les sorties médicales générées.

## Installation

```bash
python -m pip install -e '.[tracking]'
```

La version `mlflow==3.16.0` est épinglée. Le backend est une base SQLite locale
`artifacts/mlflow/mlflow.db` et les artefacts autorisés sont placés sous
`artifacts/mlflow/artifacts/`. Le backend fichiers MLflow historique n'est pas utilisé,
car MLflow 3.16 le place en maintenance et le refuse par défaut. Aucun serveur, compte
externe ou secret n'est nécessaire pour le POC.

## Import du run v39

```bash
PYTHONPATH=src python scripts/track_training_run.py \
  --config configs/sft-v2.2-final-pilot.json \
  --summary artifacts/kaggle/sft-v22-v39-reports/source-sft-v2-pilot/summary.json \
  --dataset-manifest data/manifests/derived-source-medical-qa-sft-v2.2-privacy-finalized.json \
  --stage-metric base=artifacts/kaggle/sft-v22-v39-reports/source-sft-v2-pilot/base.json \
  --stage-metric pilot_end=artifacts/kaggle/sft-v22-v39-reports/source-sft-v2-pilot/pilot_end.json \
  --tracking-directory artifacts/mlflow \
  --experiment-name chsa-medical-triage-poc \
  --run-name sft-v2.2-kaggle-v39
```

La commande refuse une divergence de checksum entre configuration, résumé et manifeste,
ainsi que tout run déclarant l'utilisation du test. Les rapports de génération restent hors
des artefacts MLflow ; seules leurs métriques agrégées sont importées.

Le run v39 a été importé avec l'identifiant
`cfd17672b87849738a178b556c2043a3`. La base SQLite contient les NLL Base et
pilote, 150 étapes et 392 tenseurs modifiés. Les seuls artefacts copiés sont la
configuration, le résumé text-free et le manifeste de données ; aucun `base.json`,
`pilot_end.json` ou texte généré n'est présent dans le store.

Le DPO v41 a été importé avec l'identifiant
`1009a86e35c64021a75b572a9448f23d`. Le store contient uniquement les métriques
agrégées de loss, préférence, durée et tenseurs modifiés, ainsi que le résumé text-free,
le handoff SFT et la preuve de poids sauvegardés. Les paires `chosen/rejected`, le trainer
state complet et les sorties générées ne sont pas journalisés.

## Limites

Le store local améliore la traçabilité et la reprise, mais ne constitue pas une sauvegarde
distante. Avant un usage d'équipe, il faudrait choisir un backend autorisé, définir ses accès,
sa rétention et son chiffrement. MLflow ne valide ni la qualité clinique ni la confidentialité
des artefacts qu'on lui donne : cette implémentation applique donc une liste minimale.
