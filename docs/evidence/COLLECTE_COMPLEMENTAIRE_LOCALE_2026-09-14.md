# Preuve locale — collecte complémentaire explicite

Date : 2026-09-14 — Statut : draft
Sources : tests/test_collection.py, tests/test_api.py, tests/test_serving.py ; ADR-015.
Environnement : macOS, Python 3.13, environnement virtuel du projet, FastAPI TestClient ; aucun modèle GPU ni endpoint extérieur appelé.
Version : API 0.3.0, prompt `triage-demo-v5-proposed`, contrôles `schema-privacy-collection-v4`.

## Question et protocole

Vérifier qu'un contexte synthétique peut évoluer sur trois appels FR/EN, que les réponses et inconnues explicites ne sont pas redemandées, et que les nouveaux champs sont anonymisés avant transport et audit.

Commande : `PYTHONPATH=src python -m pytest -q tests/test_collection.py tests/test_api.py tests/test_serving.py`.

## Résultat observé

24 tests passent en 6,65 secondes. Un avertissement de dépréciation Starlette/httpx est présent. Les contrôles couvrent : trois appels par langue, conservation de la priorité simulée `maximum` malgré une collecte incomplète, audit exact de chaque sortie, absence distincte d'information indisponible, refus des statuts contradictoires ou hors vocabulaire, constantes nulles et âge inconnu restant non renseignés, anonymisation des quatre nouveaux champs libres.

Ruff passe sur les fichiers modifiés après correction du formatage. Le test du runner d'évaluation est adapté au nouveau contrat de réponse obligatoire `collection`. La régression complète `PYTHONPATH=src python -m pytest -q` passe : **163 tests en 7,48 secondes**, même avertissement de dépréciation. La réservation `val_fd3d564d8f79` est terminée avec code 0 ; créneau libéré et processus propriétaire arrêté. La révision testée est `1756f1b`.

## Limites et suite

Le fournisseur et le détecteur de confidentialité des tests sont simulés. Cette preuve établit le contrat et l'orchestration locale ; elle n'établit ni l'efficacité de Presidio sur toute donnée personnelle, ni la qualité des réponses du modèle avec le prompt v5, ni une validation clinique, ni un parcours d'interface rendu. Les mesures GPU v34 concernent exclusivement le code antérieur. L'évaluation QA v35 en cours utilise son paquet figé antérieur et reste indépendante.

Prochaine étape : terminer la régression complète, puis mesurer le parcours enrichi avec le modèle réel. Les questions générées librement par le modèle restent distinctes du suivi déterministe des rubriques.
