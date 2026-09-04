# Contribuer

Ce dépôt est un POC scolaire public. Toute contribution doit préserver ses limites : aucune donnée patient, aucun secret, aucune affirmation clinique non prouvée et aucun poids de modèle volumineux.

## Préparer une contribution

1. Créer une branche courte depuis `main`.
2. Installer le projet avec `pip install -e '.[dev]'`.
3. Ajouter ou adapter les tests et la documentation correspondante.
4. Exécuter :

```bash
python -m pytest
python -m ruff check src scripts tests
git diff --check
```

5. Utiliser un commit Conventional Commits, par exemple `feat(data): add deterministic source filter`.

## Données et résultats

- Ne jamais committer `data/raw/`, `data/processed/`, `artifacts/`, `models/` ou `checkpoints/`.
- Une nouvelle source exige un manifeste avec URL, révision, licence, citation, checksum et restrictions.
- Une mesure doit indiquer l'environnement, les versions, la commande, le résultat et ce qu'elle ne prouve pas.
- Une cible de triage non revue doit rester explicitement `proposed` ou `not_performed`.

## Pull requests

Décrire le problème, la solution, les tests exécutés, les impacts sur les données et les limites cliniques. Les changements ne doivent jamais transformer ce POC en outil destiné à un usage patient réel.
