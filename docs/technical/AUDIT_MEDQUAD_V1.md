# Audit MedQuAD v1

- **Date :** 2026-08-31
- **Statut :** implemented and observed on pinned revision
- **Sources :** `src/triage_poc/medquad_audit.py`, `scripts/audit_medquad.py`, `scripts/audit_medquad_presidio_sample.py`

## Fonctionnement

L’audit parcourt les XML du checkout MedQuAD épinglé et produit uniquement des agrégats : volumes, réponses vides, doublons de questions normalisées, XML malformés et comptes de motifs email/téléphone. Aucun texte, span ou identifiant détecté n’est écrit dans le rapport.

Un second script sélectionne de façon déterministe dix paires non vides par sous-ensemble admissible, à partir du hash du chemin source et du `pid`. Presidio analyse et anonymise ces 90 textes en anglais. Le rapport conserve seulement les comptes d’entités, les statuts résiduels et le hash de sélection.

## Commandes reproductibles

```bash
PYTHONPATH=src .venv/bin/python scripts/audit_medquad.py \
  --repository data/raw/medquad \
  --output artifacts/medquad-candidate-audit-2026-08-31.json

PYTHONPATH=src .venv/bin/python scripts/audit_medquad_presidio_sample.py \
  --repository data/raw/medquad \
  --output artifacts/medquad-presidio-sample-2026-08-31.json \
  --sample-per-subset 10

PYTHONPATH=src .venv/bin/python scripts/prepare_medquad_review_queue.py \
  --repository data/raw/medquad \
  --output data/processed/medquad-review-queue-v1.json \
  --limit 200
```

## File d’aide à la rédaction

Le troisième script sélectionne en round-robin déterministe des questions `symptoms` parmi les sous-ensembles autorisés, déduplique les questions normalisées, anonymise séparément question et réponse et rejette toute détection résiduelle. La sortie est hors Git et chaque entrée conserve `triage_target: null`, `clinical_review_status: not_started` et `allowed_use: clinical_scenario_authoring_candidate_only`.

Le run observé a conservé 193 entrées sur 200 et en a rejeté 7 pour PII résiduelle. Cette file aide un réviseur à rédiger des scénarios ; elle ne satisfait pas le schéma SFT et ne peut pas passer le pré-vol d’entraînement.

## Limites

Le regex ne distingue pas un numéro institutionnel d’une donnée personnelle. Le sample Presidio ne couvre pas tout le corpus et ses entités `PERSON`, `LOCATION` ou `DATE_TIME` peuvent être des faux positifs médicaux. Une revue humaine et un contrôle du corpus sélectionné restent obligatoires avant toute admission.
