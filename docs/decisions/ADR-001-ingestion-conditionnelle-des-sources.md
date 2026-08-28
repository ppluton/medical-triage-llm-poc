# ADR-001 — Ingestion conditionnelle des sources de données

- **Date :** 2026-08-28
- **Statut :** proposed
- **Décideur :** projet d'étude POC Agent IA de triage médical

## Contexte

La spécification cite quatre sources de données. Le projet est public, médical et orienté triage ; un téléchargement immédiat sans provenance, licence, contrôle PII, split et justification d'usage compromettrait la reproductibilité et la sûreté du POC.

## Décision

Conserver les quatre sources comme candidates sous contrôle. N'ingérer aucun fichier tant que les sept critères d'acceptation du registre de gouvernance ne sont pas satisfaits pour le sous-ensemble concerné. Épingler une version immuable et créer un manifeste avant toute transformation.

## Alternatives écartées

- Télécharger et fusionner les quatre datasets immédiatement : rejeté, car il masque les licences, formats, restrictions et risques propres à chaque source.
- Écarter d'emblée toutes les sources externes : rejeté, car cela empêcherait d'étudier la faisabilité demandée sans preuve qu'elles sont inutilisables.

## Conséquences

- Le démarrage est plus lent, mais les données utilisées et les résultats sont auditables.
- Le dataset final pourra contenir moins que les 5 000 paires visées si les contrôles excluent des sous-ensembles ; cette limite devra être rapportée, pas contournée.
- Une validation clinique reste requise pour les transformations destinées à produire une priorité ou une recommandation de triage.
