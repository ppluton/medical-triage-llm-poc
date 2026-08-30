# ADR-005 — Reconstruire les splits DPO UltraMedical-Preference

- **Date :** 2026-08-31
- **Statut :** approved for candidate processing only
- **Propriétaire :** équipe POC
- **Statut clinique :** not approved
- **Sources :** `data/manifests/src-ultramedical-preference-761eb79.json`, dataset `TsinghuaC3I/UltraMedical-Preference`

## Contexte

UltraMedical-Preference fournit 112 362 paires de préférence biomédicales au format conversationnel. Le split de test contient un benchmark dont 163 paires portent un label humain. L'audit normalisé trouve cependant 1 228 prompts communs entre `train` et `dev`, 30 entre `train` et `test`, ainsi qu'un prompt commun entre `dev` et `test`.

Le split `train` contient aussi 33 152 instances de prompts normalisés dupliqués. Ces répétitions peuvent représenter plusieurs comparaisons pour un même prompt, mais elles empêchent de considérer les lignes comme des exemples indépendants.

## Décision

- Réserver intégralement `test` à l'évaluation et ne jamais l'utiliser pour l'optimisation.
- Retirer de `train` et `dev` tout prompt normalisé présent dans `test`.
- Retirer de `train` tout prompt normalisé présent dans `dev` après nettoyage.
- Regrouper les préférences restantes par prompt avant la sélection, plutôt que compter chaque ligne comme un scénario indépendant.
- N'admettre au DPO que des préférences compatibles avec le contrat de triage et validées par la gouvernance PII et clinique.
- Documenter le nombre de lignes perdues et les hashes de chaque split reconstruit.

## Alternatives écartées

- **Utiliser les splits tels quels :** rejeté à cause des chevauchements mesurés.
- **Déplacer le test humain vers l'entraînement :** rejeté, car cela détruirait le benchmark indépendant.
- **Employer toutes les préférences biomédicales pour le DPO de triage :** rejeté, car qualité biomédicale générale et sûreté de triage sont deux objectifs distincts.

## Conséquences

Le volume DPO utile sera inférieur aux 109 353 lignes brutes. Cette réduction est acceptable : l'indépendance de l'évaluation, la pertinence de la préférence et la traçabilité priment sur le volume annoncé. Un script de reconstruction déterministe doit précéder toute préparation DPO.
