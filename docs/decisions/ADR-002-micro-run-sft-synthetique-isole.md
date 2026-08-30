# ADR-002 — Micro-run SFT synthétique isolé

- **Date :** 2026-08-30
- **Statut :** approved for technical validation only
- **Propriétaire :** équipe POC
- **Statut clinique :** not approved
- **Sources :** `CADRAGE_MISSION.md`, `SPEC_POC_TRIAGE_MEDICAL.md`, `docs/governance/ADEQUATION_FRENCHMEDMCQA_TRIAGE.md`, `data/manifests/src-synthetic-sft-fixture.json`

## Contexte

Le POC doit vérifier progressivement son pipeline SFT/LoRA. La source FrenchMedMCQA reste `candidate` : son manifest indique des recouvrements entre splits après normalisation et une revue PII incomplète. Elle ne peut donc pas être promue ni incluse dans ce micro-run.

Deux exemples de triage sont synthétiques, soumis à des contrôles de format et PII, mais leurs cibles conservent une revue clinique `pending`.

## Décision

Autoriser un micro-run local Unsloth exclusivement sur `src-synthetic-sft-fixture.json`, avec les limites suivantes :

- objectif limité à la validation technique du chargement, de l’entraînement, du checkpoint et des artefacts ;
- fichiers `train` et `validation` préparés séparément ; aucun split `test` ;
- aucune source `candidate`, notamment FrenchMedMCQA, ne doit être sélectionnée ;
- aucune métrique, sortie ou checkpoint ne peut étayer une affirmation clinique ;
- aucune API, publication, export externe ou déploiement ne découle automatiquement du micro-run.

Le pré-vol `scripts/preflight_synthetic_sft.py` impose le manifest synthétique approuvé, le type `sft`, l’origine `synthetic`, le split demandé et le statut PII `passed`.

## Alternatives examinées

1. Promouvoir FrenchMedMCQA : rejeté, car les checks `split_leakage` et PII ne sont pas achevés.
2. Attendre toutes les données réelles : écarté pour le pipeline technique, car les fixtures synthétiques permettent déjà une preuve bornée.
3. Lancer un run sans pré-vol : rejeté, car il contournerait la séparation gouvernance/expérimentation.

## Conséquences

Le micro-run peut échouer ou sur-apprendre avec un seul exemple `train`; ce résultat ne serait pas une régression clinique. La preuve devra distinguer la réussite technique, les artefacts observés et les limites de généralisation.
