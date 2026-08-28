# Adéquation FrenchMedMCQA au triage

- **Statut :** decision proposed

FrenchMedMCQA contient des QCM de pharmacie avec réponses correctes. Ce format peut contribuer à une évaluation de connaissances médicales francophones, mais ne fournit pas les éléments nécessaires à une cible de triage : contexte symptomatique complet, priorité validée, justification clinique, informations manquantes, signal d'alerte et recommandation encadrée.

## Décision proposée

- Ne pas convertir automatiquement les QCM en enregistrements SFT ou paires DPO de triage.
- Ne pas utiliser ses splits reconstruits comme jeu d'évaluation clinique de triage.
- Conserver la source comme candidate de connaissance générale, sous conditions de PII et revue restantes.
- Construire séparément des scénarios de triage synthétiques puis les soumettre à revue clinique.

Cette décision évite de présenter une précision de QCM comme une capacité de triage médical.
