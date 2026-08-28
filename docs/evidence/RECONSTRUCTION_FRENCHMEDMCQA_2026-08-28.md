# Preuve — reconstruction des splits FrenchMedMCQA

- **Statut :** partially_proven
- **Entrée :** archive candidate `src-frenchmedmcqa-deft-2023-full`
- **Sortie :** `data/processed/frenchmedmcqa-rebuilt/`, ignorée par Git

La reconstruction déterministe par question normalisée a produit 2 191 exemples `train`, 447 `validation` et 467 `test`. Aucun chevauchement de question normalisée n'a été observé entre les trois sorties.

Cette preuve corrige uniquement la fuite textuelle exacte. Le dataset dérivé reste `candidate` : contrôles PII Presidio, déduplication sémantique, traçabilité de transformation détaillée et revue clinique restent nécessaires avant toute utilisation d'entraînement ou d'évaluation.
