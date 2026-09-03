# ADR-008 — Séparer l'adaptation médicale SFT des préférences de triage DPO

- **Date :** 2026-09-03
- **Statut :** approved for educational implementation
- **Propriétaire :** porteur du projet d'étude
- **Statut clinique :** not validated
- **Sources :** cadrage, spécification, manifestes MedQuAD, MediQAl, FrenchMedMCQA et UltraMedical-Preference

## Contexte

Les trois corpus de questions-réponses contiennent des connaissances médicales, mais aucun ne fournit une vérité terrain pour les niveaux de triage `maximum`, `moderate` et `deferred`. UltraMedical-Preference fournit des préférences de réponses et correspond à l'étape DPO, pas au SFT de questions-réponses.

Le dataset synthétique précédent prouve que le pipeline technique sait produire 5 000 lignes structurées. Il ne doit cependant pas être présenté comme le dataset SFT final fondé sémantiquement sur les corpus.

## Décision

- Construire le SFT de 5 000 exemples avec les questions et réponses effectivement fournies par MedQuAD, MediQAl et FrenchMedMCQA.
- Obtenir un équilibre de 2 500 exemples anglais et 2 500 français : 2 500 MedQuAD, 1 500 MediQAl et 1 000 FrenchMedMCQA.
- Réserver UltraMedical-Preference à un dataset DPO séparé.
- Ne générer aucun label de triage à partir des réponses QA.
- Isoler 4 000 lignes `train`, 500 `validation` et 500 `test`. Le test n'est jamais rendu au format d'entraînement.
- Conserver le dataset synthétique protocolisé comme fixture d'expérimentation technique, désormais supplantée pour le SFT principal.

## Conséquences

Le premier entraînement complet devient une adaptation au domaine médical et au format instruction-réponse. Il ne suffit pas à prouver que le modèle sait trier. Le DPO et l'évaluation de sûreté devront ensuite mesurer et améliorer le comportement de triage sans transformer une réponse de QCM en label clinique inventé.

Cette séparation rend l'explication du projet simple : **SFT = connaissances et format médicaux ; DPO = préférences de prudence ; évaluation = mesure du triage**.

## Limites

- Les réponses sont publiées par les sources, mais n'ont pas été revues cliniquement dans ce projet.
- Une réponse source peut être incomplète ou datée.
- Le passage Presidio est un contrôle technique d'anonymisation, pas une certification RGPD.
- L'équilibre linguistique est un choix de projet, pas une garantie d'équivalence de difficulté entre français et anglais.
