# Lisibilité et provenance du résultat de démonstration

Date : 2026-10-08 · Statut : contrôles locaux réalisés, livraison suivie séparément
Sources : tests/test_api.py, code frontend, captures locales de validation non publiées.

## Périmètre

Afficher la provenance réelle du résultat final et rendre le parcours de collecte compréhensible. Les poids, les priorités et les garde-fous restent inchangés.

## Preuves locales

- `python -m pytest -q` : 253 tests passent. Le nouveau test vérifie les trois statuts API et l’absence d’exposition des motifs internes et du texte brut.
- `python -m ruff check src scripts tests deploy` et `node --check src/triage_poc/demo_ui/app.js` : réussis.
- Navigateur Chromium sur le checkout courant, 1440 × 1000 puis 390 × 844 : résultat de repli explicite, absence du message d’attente après réponse, aucune largeur débordante sur mobile, bascule de scénario sans ancien résultat, libellés FR/EN, réponse à la collecte avec absence confirmée et information indisponible.
- Backend de validation local : fournisseur synthétique sans GPU. Ces contrôles prouvent le rendu et le contrat local, pas une inférence du modèle.

## Limites

La conservation d’une proposition ne garantit pas sa justesse clinique. L’interface n’expose pas le texte brut avant contrôle. Les déploiements et appels authentifiés externes constituent une étape distincte.
