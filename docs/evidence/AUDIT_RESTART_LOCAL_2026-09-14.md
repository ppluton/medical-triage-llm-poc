# Audit : synchronisation et redémarrage local

Date : 2026-09-14 — Statut : draft
Sources : ADR-013, tests/test_audit_restart.py, tests/test_serving.py, src/triage_poc/serving.py.
Environnement : macOS, Python 3.13, FastAPI TestClient dans deux processus indépendants ; modèle simulé ; cas synthétiques exclusivement.

## Mesure

Commande : `PYTHONPATH=src python -m pytest -q tests/test_audit_restart.py tests/test_serving.py`.
Résultat : **14 tests passent en 17,43 secondes**, avec un avertissement de dépréciation Starlette/httpx. Ruff passe sur le sink et le nouveau test.

Chaque processus crée sa propre application, effectue un appel `POST /v1/triage`, puis s'arrête. Les deux réponses HTTP réussies correspondent exactement aux deux sorties du même journal JSONL après le second processus. Leurs identifiants sont distincts et le fichier créé est en mode 0600.

Une simulation séparée fait échouer `fsync` : l'API retourne 503 sans proposition de triage. Les tests existants vérifient également les refus d'anonymisation, les erreurs de génération et les erreurs d'écriture.

## Version et limites

L'évolution ajoute `os.fsync` après l'écriture complète et avant la fermeture du fichier ; le chemin de refus d'audit existant reste utilisé. Aucun effacement, aucune durée de rétention et aucune publication ne sont ajoutés.

Preuve établie : conservation locale des deux échanges après arrêt normal et recréation du processus API, et refus de restitution si la synchronisation échoue. Non établi : résistance à une panne électrique, corruption, perte de volume, concurrence intensive, stockage distant, vraie inférence ou validation clinique. Une ligne éventuellement présente après un échec de synchronisation ne démontre pas sa réception par le client.

Suite : reproduire la persistance sur le volume de la cible autorisée, définir sa rétention et vérifier le raccord au modèle réel. Le paquet API candidat précédemment préparé précède cet ajout et doit être régénéré avant son prochain lancement.
