# Preuve locale — anonymisation v1

- **Date :** 2026-08-28
- **Statut :** partially_proven
- **Branche :** `codex/medical-triage-anonymization`
- **Périmètre :** module `src/triage_poc/anonymization.py`

## Claim vérifié

Le module applique une politique fail-closed, remplace les entités détectées, ne conserve pas le texte source dans son audit et signale une PII résiduelle pour revue manuelle.

## Environnement et commandes

- macOS, Python 3.13.3
- `presidio-analyzer` 2.2.364
- `presidio-anonymizer` 2.2.364
- `pytest` 8.4.2
- `ruff` 0.16.5

```bash
.venv/bin/python -m pytest
.venv/bin/python -m ruff check src tests
```

## Résultats observés

- **Proven :** 5/5 tests unitaires passent.
- **Proven :** le lint des fichiers `src` et `tests` passe.
- **Proven :** les tests couvrent le remplacement d'une référence patient synthétique et d'un email synthétique, la détection résiduelle, les entrées vides, les langues non supportées et une erreur de détecteur.
- **Non prouvé :** le comportement de Presidio avec les modèles spaCy réels. Le téléchargement de `fr_core_news_md` a été lancé, mais le modèle n'était pas installé à la vérification suivante ; aucun test d'intégration NER n'est donc déclaré vert.

## Limites

Ces résultats portent uniquement sur des données synthétiques et des doubles de test. Ils ne mesurent ni le rappel des PII sur un dataset externe, ni une conformité RGPD, ni une validation clinique.

## Prochaine preuve requise

Installer les modèles spaCy épinglés, exécuter des scénarios synthétiques français et anglais avec le moteur Presidio réel, puis consigner séparément les entités attendues, détectées et manquées.
