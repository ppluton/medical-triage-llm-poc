# Audit local des entrées et sorties de l'API

- Date : 2026-09-12
- Statut : draft — intégration locale testée, modèle et anonymiseur simulés
- Environnement : macOS, branche `codex/complete-poc-evaluation`, Python 3.13 du projet avec `PYTHONPATH=src`.
- Sources : [ADR-013](../decisions/ADR-013-audit-entree-sortie-anonymisees.md), `tests/test_serving.py`, `tests/test_api.py`.

## Claim et modification

Une interaction réussie conserve dans le JSONL le contexte anonymisé transmis au
modèle et la réponse délivrée, avec le même identifiant. Tous les champs textuels
du résultat passent par le contrôle d'anonymisation avant réponse et audit.
L'enveloppe `ProviderResult` relie explicitement résultat, version et contexte à la
requête courante ; aucun état « dernière requête » n'est partagé sur le fournisseur.

Avant correction, un test avec email synthétique dans la réponse simulée échouait :
l'email restait visible dans la réponse HTTP. Après correction, l'email est masqué
et le JSONL contient l'entrée anonymisée et la sortie identique au JSON HTTP.

## Vérification exécutée

```sh
PYTHONPATH=src python -m pytest tests/test_api.py tests/test_serving.py \
  tests/test_endpoint_evaluation.py tests/test_triage_probe.py -q
ruff check src/triage_poc/api.py src/triage_poc/serving.py \
  tests/test_api.py tests/test_serving.py
```

Résultat : **16 passed**, Ruff passant. Une dépréciation Starlette/httpx est signalée,
sans échec. Les tests vérifient aussi le refus de délivrance après échec du contrôle
de sortie (502, audit sans contenu) et après échec de stockage malgré une inférence
simulée réussie (503). Les détails internes de ces erreurs ne sont pas retournés.

## Portée et limites

Prouvé localement : trajet API → fournisseur avec transport HTTP simulé → fichier
JSONL réel → réponse client ; contrat d'échec ; masquage avec un anonymiseur de test.
Non prouvé ici : efficacité exhaustive de Presidio, inférence vLLM, conservation sur
un hébergement, accès au fichier en déploiement, politique de rétention ni validité
clinique. Les requêtes rejetées par validation FastAPI (422) et authentification
(401) n'empruntent pas ce journal d'interaction ; leur suivi opérationnel reste séparé.

Les erreurs n'enregistrent aucune entrée brute pour tenter de compenser un contrôle
qui n'a pas abouti. Le corpus, les poids et le run Kaggle en cours sont inchangés.
