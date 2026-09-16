# Réancrage du lot DPO sur le corpus SFT v2.2

- Date : 2026-09-16
- Statut : verified_for_educational_dpo
- Statut clinique : not_performed
- Sources : manifeste SFT v2.2, lot DPO v2, décision technique de réancrage et manifeste DPO v3.

## Question

Le lot de préférences historique protège-t-il encore exactement le corpus SFT après
le masquage de 31 occurrences de noms dans 22 lignes de la version v2.2 ?

## Observation initiale

Les 480 prompts DPO restaient disjoints des 4 200 instructions SFT train et validation.
Cependant, 17 instructions modifiées par le masquage n'étaient plus présentes dans
l'ensemble d'empreintes protégé par le manifeste DPO v2. Le lot n'était donc pas
corrompu, mais sa preuve de lignée était devenue incomplète. Parmi les cinq autres
lignes masquées, quatre appartenaient au test isolé et une ligne train ne changeait
que la réponse, sans modifier l'empreinte de son instruction.

## Correction reproductible

`finalize_dpo_review.py` exige désormais le canonique SFT courant. Il vérifie son
checksum et son nombre de lignes contre le manifeste, refuse les identifiants ou les
instructions non uniques, recalcule les 4 700 empreintes normalisées et les ajoute à
l'ensemble protégé. La décision de revue doit correspondre à la fois au manifeste
DPO parent, au manifeste SFT et au canonique SFT.

Commande exécutée :

```bash
PYTHONPATH=src .venv/bin/python scripts/finalize_dpo_review.py \
  --source artifacts/dpo-reviewed-v2 \
  --output artifacts/dpo-reviewed-v3-v22-bound \
  --sft-manifest data/manifests/derived-source-medical-qa-sft-v2.2-privacy-finalized.json \
  --sft-canonical data/processed/source-sft-v2.2-privacy-finalized/source-sft-v2.2.jsonl \
  --decision docs/evidence/DPO_V22_REBIND_DECISION_2026-09-16.json \
  --decision-id ADR-017 --review-date 2026-09-16 \
  --manifest-id derived-ultramedical-dpo-v3-v22-bound
```

## Résultat observé

- 426 paires train et 54 paires validation ;
- 480/480 champs d'entraînement et de provenance inchangés ;
- zéro recouvrement entre les 480 prompts DPO et les 4 700 instructions SFT v2.2 ;
- 4 700/4 700 empreintes SFT courantes présentes dans l'ensemble protégé ;
- 8 343 empreintes protégées au total, anciennes protections conservées ;
- zéro réponse du test utilisée ;
- 11 tests DPO ciblés réussis et Ruff réussi.

## Portée

Cette preuve rétablit l'isolation technique et la lignée des données avant un futur
run DPO fondé sur le SFT v2.2. Elle ne valide pas les préférences médicalement, ne
démontre aucun gain du DPO et n'autorise pas l'ouverture du jeu de réserve final.
