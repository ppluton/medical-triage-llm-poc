# Vérifier la correspondance entre réponse API et audit

- Date : 2026-09-12
- Statut : draft — contrôle local ; aucune exécution cloud
- Sources : `scripts/verify_endpoint_audit.py`, `tests/test_endpoint_audit.py`, [guide](../../technical/EVALUATION_ENDPOINT_V1.md).

Le contrôle compare chaque réponse réussie du rapport d'évaluation à une seule entrée
du journal fourni. Les sorties différentes, entrées absentes/dupliquées, versions
manquantes, statuts de confidentialité non passés et lots sans succès sont refusés.
Les empreintes SHA-256 des fichiers fixent les entrées de la preuve. Aucun texte du
journal n'est recopié dans le résultat.

Commande locale : `PYTHONPATH=src python -m pytest tests/test_endpoint_audit.py -q`.
Résultat : deux tests réussis en 7,74 s ; avertissement Starlette/httpx de dépréciation.
Ruff passe. Deux tests couvrent les divergences ainsi qu'une vraie réponse FastAPI TestClient
rapprochée du fichier JSONL écrit par JsonlAudit. Le modèle est un fournisseur
synthétique, sans inférence ni preuve d'anonymisation réelle. Une altération du fichier
après écriture est détectée. Ces tests ne prouvent pas un déploiement ni la durabilité
du stockage cloud ; ils rendent cette prochaine vérification reproductible.
