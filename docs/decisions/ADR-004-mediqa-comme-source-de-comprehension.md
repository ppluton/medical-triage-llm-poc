# ADR-004 — MEDIQA comme source candidate de compréhension médicale

- **Date :** 2026-08-31
- **Statut :** superseded par ADR-006
- **Propriétaire :** équipe POC
- **Statut clinique :** not approved
- **Sources :** `data/manifests/src-mediqa2019-32311a1.json`, dépôt `abachaa/MEDIQA2019`

## Contexte

MEDIQA 2019 fournit des tâches de reconnaissance d'entailment entre questions médicales (RQE) et de classement de réponses (QA). Le mandat cite cette source, mais le contrat du POC attend une priorité parmi `maximum`, `moderate` et `deferred`, un raisonnement encadré et une recommandation de sécurité.

L'audit de la révision épinglée trouve 9 120 paires RQE, 383 questions QA et 3 042 réponses dans les exports canoniques. Les labels disponibles décrivent l'entailment ou la pertinence d'une réponse, jamais une priorité de triage.

## Décision

- Conserver les tâches 2 RQE et 3 QA au statut `candidate`.
- Exclure la tâche 1 MedNLI, absente du dépôt et soumise à l'accès PhysioNet.
- Utiliser éventuellement les questions anonymisées pour diversifier la formulation de scénarios ou construire une évaluation auxiliaire de compréhension.
- Interdire la conversion automatique des labels RQE/QA en niveaux de triage.
- Préserver les splits natifs et dédupliquer avant toute sélection.
- Exiger une revue clinique séparée pour chaque cible de triage dérivée.

## Alternatives écartées

- **Convertir `true/false` en urgent/non urgent :** rejeté, car l'entailment ne mesure pas l'urgence.
- **Convertir les scores QA 1–4 en niveaux de triage :** rejeté, car ces scores mesurent la qualité d'une réponse.
- **Inclure MedNLI via une autre copie :** rejeté sans accès et gouvernance spécifiques à PhysioNet.

## Conséquences

MEDIQA augmente la couverture linguistique et la variété des questions candidates, mais ne résout pas la création des labels cliniques. Le corpus SFT final restera bloqué sur une validation clinique explicite des scénarios et des cibles.

Depuis le 3 septembre 2026, cette décision est conservée comme historique. Le corpus prescrit est clarifié comme étant MediQAl dans ADR-006 ; MEDIQA 2019 n'entre plus dans la file courante.
