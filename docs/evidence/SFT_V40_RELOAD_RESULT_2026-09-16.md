# Résultat de la recharge SFT v39 — Kaggle v40

- Date : 2026-09-16
- Statut : pilot_fresh_reload_verified
- Notebook privé : `pierrepluton/chsa-source-sft-qwen3`, version 40
- Étapes d'optimisation : 0
- Test utilisé : 0
- Statut clinique : not_performed

## Recharge principale

Le checkpoint 150 a été rechargé dans un nouveau processus GPU. Ses cinq checksums de
reprise correspondent exactement au résumé v39. Les trente générations greedy sont
identiques octet pour octet et le delta absolu de NLL sur les 479 validations vaut `0.0`.
Les 392 tenseurs entraînables restent en FP32 pendant chaque phase d'évaluation.

Le manifeste [SFT v39](../../configs/sft-v39-handoff.json) lie l'adaptateur
`c911f9c…5d413`, le tokenizer, le template, la révision Base, le manifeste de données
v2.2 et les résumés v39/v40. Il ne constitue pas une approbation clinique.

## Comparaison des checkpoints

| Étape | NLL validation | EOS / 30 | Plafond / 30 | Exact / 30 | Répétition 4-grammes |
|---:|---:|---:|---:|---:|---:|
| 50 | 0,822172 | 26 | 4 | 6 | 0,1404 |
| 100 | 0,730402 | 25 | 5 | 6 | 0,1661 |
| 150 | 0,711802 | 22 | 8 | 7 | 0,2385 |

L'étape 150 minimise la NLL et ajoute une correspondance exacte, tandis que l'étape 50
termine mieux et répète moins. Il n'existe donc pas de domination sur toutes les métriques.
La v41 utilise l'étape 150 comme candidat DPO borné afin de conserver le critère primaire
d'ajustement à la réponse, mais l'étape 50 est retenue comme alternative si la comparaison
post-DPO confirme une dégradation de forme. Ce choix expérimental n'est pas une décision
clinique et ne garantit pas un bénéfice DPO.

## Portée

Cette preuve ferme la reproductibilité technique du SFT v39. Elle n'ouvre pas la réserve
finale et ne démontre ni pertinence de triage, ni sûreté clinique, ni supériorité de l'étape
150 sur tous les comportements.
