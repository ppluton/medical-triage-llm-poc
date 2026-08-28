# Rapport technique — POC Agent IA de triage médical

- **Statut :** draft, aucun résultat clinique déclaré
- **Limite :** maximum 20 pages une fois finalisé

## 1. Résumé exécutif

À compléter avec le périmètre réellement démontré, les métriques et les limites.

## 2. Contexte et limites de responsabilité

POC d'assistance au triage ; ni dispositif médical, ni diagnostic, ni prescription, ni décision autonome.

## 3. Données et gouvernance

Sources, licences, révisions, anonymisation, splits, exclusions et revue clinique.

## 4. Méthode

Baseline Qwen, SFT/LoRA, DPO, versions, hyperparamètres et reproductibilité.

## 5. Évaluation

Matrice de confusion, sous-triage, sur-triage, rappel des cas `maximum`, robustesse et latence. Toute référence non revue cliniquement doit être signalée.

## 6. API, audit et sécurité

Contrat API, garde-fous, minimisation des logs, conteneurisation et CI.

## 7. Résultats et limites

Ne rapporter que des résultats liés à une exécution identifiée. Distinguer test automatisé, exécution d'inférence, revue humaine et validation clinique.

## 8. Roadmap go / no-go

Conditions de poursuite : données approuvées, validation clinique, tests de sûreté, architecture d'hébergement, conformité et monitoring.
