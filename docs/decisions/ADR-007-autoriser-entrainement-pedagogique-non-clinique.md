# ADR-007 — Autoriser l'entraînement pédagogique sans validation clinique

- **Date :** 2026-09-03
- **Statut :** approved for educational experimentation
- **Propriétaire :** porteur du projet d'étude
- **Statut clinique :** not validated
- **Sources :** cadrage du POC, spécification, FRENCH 2018 v1.2, principes HAS de triage aux urgences, protocole `educational-triage-protocol-v1`

## Contexte

Le projet est réalisé dans un cadre scolaire par un AI Engineer/Data Scientist sans accès à un référent clinique. Exiger une approbation médicale avant toute expérimentation rendrait impossible le livrable technique, alors que le mandat demande précisément de démontrer une chaîne SFT, DPO, évaluation et API.

À l'inverse, déclarer les cibles générées « validées cliniquement » serait faux. Il faut donc séparer l'autorisation d'expérimenter de la validation nécessaire à un usage médical.

## Décision

- Autoriser la génération et l'entraînement local sur des scénarios synthétiques portant des cibles `proposed_protocol_generated`.
- Conserver `clinical_review_status: pending` sur tous les enregistrements qui n'ont pas été revus par un professionnel qualifié.
- Employer le statut d'usage `educational_poc_training_only` dans le futur manifeste dérivé.
- Autoriser les métriques uniquement par rapport aux références expérimentales proposées.
- Interdire toute conclusion de sûreté clinique, toute utilisation patient et toute présentation comme dispositif médical.
- Exiger un hash du protocole, du dataset, du code et des splits pour chaque run.

## Alternatives écartées

- **Attendre un médecin avant d'entraîner :** incompatible avec le contexte et le calendrier scolaire.
- **Marquer les exemples `approved` cliniquement :** faux et contraire aux règles du dépôt.
- **Supprimer toute référence clinique :** incompatible avec l'objectif de triage du POC.
- **Utiliser directement les labels QA comme priorités :** les corpus sources n'annotent pas le triage.

## Conséquences

Le projet peut terminer son cycle technique et produire des résultats reproductibles. Ces résultats démontreront une faisabilité d'ingénierie sur un benchmark expérimental ; ils ne démontreront pas une pertinence clinique.

Une future revue médicale ne sera pas une formalité rétroactive : elle pourra modifier le protocole, invalider des cibles et imposer un nouvel entraînement.
