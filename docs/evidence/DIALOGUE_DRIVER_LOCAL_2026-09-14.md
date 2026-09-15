# Vérification locale du pilote de dialogue API

Date : 2026-09-14 — Statut : draft
Sources : src/triage_poc/dialogue_evaluation.py, scripts/evaluate_collection_endpoint.py, tests/test_dialogue_evaluation.py, data/samples/synthetic-collection-dialogues-v1.json.
Environnement : macOS, Python 3.13, FastAPI TestClient et fournisseur simulé ; fixtures synthétiques FR/EN de développement.

## Protocole et résultat

Commande : `PYTHONPATH=src python -m pytest -q tests/test_dialogue_evaluation.py`.
Résultat : **6 tests passent en 14,08 secondes**, un avertissement de dépréciation Starlette/httpx. Ruff passe après correction de formatage.

Le pilote utilise les questions effectivement renvoyées par l'API pour choisir les réponses de sa fixture. Deux dialogues, six appels chacun, aboutissent à la fin de la collecte. Les symptômes initiaux et les réponses cumulées sont préservés ; les douze sorties correspondent à leurs audits. Un faux serveur répétant ses premières questions avec de nouveaux identifiants est détecté au deuxième appel. Un échec HTTP reste un échec, sans recopier son corps. Une fixture non synthétique ou une réponse invalide est refusée avant transport.

Les dialogues reprennent les cas synthétiques FR/EN de gêne stable du poignet déjà présents dans le lot de développement. Durée, évolution, intensité et absence de symptômes associés sont explicites ; les autres informations sont déclarées indisponibles. Aucune priorité clinique de référence supplémentaire n'est créée.

## Préparation GPU

Le runner vLLM exécute maintenant, pour Base, SFT puis DPO, le lot de 18 appels puis les deux dialogues, avec rapprochement d'audit pour chaque lot. Cela représente 90 appels si aucun dialogue n'est interrompu. Il conserve les codes d'échec et les empreintes des deux fichiers de scénarios. Aucun entraînement ni test réservé n'est utilisé.

Paquet local `artifacts/kaggle/api-dialogue-candidate`, notebook SHA-256 `3f5a79ec62eebfca17a6e1e726b08d145e95b6424f7e996bc8d1c19a40b3e2ff` : 42 fichiers comparés au checkout, Python compilé, synchronisation d'audit incluse. **Préparé, non lancé.** Il remplace le candidat antérieur pour un prochain essai.

## Limites

La réussite du pilote prouve le suivi technique des rubriques, pas la pertinence clinique des priorités, explications ou questions libres du modèle. Les réponses aux questions sont prédéfinies pour le test, pas celles d'un vrai patient. La preuve GPU du dialogue reste à produire. Les scores v34 et le test QA v35 sont des mesures distinctes et ne doivent pas être réattribués à ce nouveau code.
