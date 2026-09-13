# Régression locale après DPO et préparation du service

- Date : 2026-09-13
- Statut : draft — tests locaux réussis, inférence distante non couverte
- Sources : journal `val_4a5cf8de3d3b`, tests du dépôt et Ruff.

Révision testée : `1784df4`, branche `codex/complete-poc-evaluation`.
Environnement : macOS, Python 3.13 du venv du projet, `PYTHONPATH=src` explicite
pour charger ce worktree. Commande : `python -m pytest -q` sous réservation
`codex-validate`, résultat 138 passed en 4,58 secondes, code 0.
Un avertissement de dépréciation Starlette/httpx est présent ; aucun test échoue.
`ruff check src scripts tests` retourne également 0.

La réservation est terminée, slot libéré. Les tests couvrent les contrats et
transformations locales, dont les vérificateurs de métriques et d'audit ; leurs
fournisseurs simulés ne prouvent pas une inférence du vrai modèle. La suite ne
lance ni entraînement GPU ni endpoint cloud et ne mesure aucune performance
clinique. Les résultats v28 et les preuves de service réel restent nécessaires.
