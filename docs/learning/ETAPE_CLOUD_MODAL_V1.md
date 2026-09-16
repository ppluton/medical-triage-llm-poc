# Préparer une démonstration GPU à coût borné

- Date : 2026-09-16
- Statut : `draft`
- Sources : documentation Modal officielle citée dans
  `docs/technical/MODAL_DEPLOYMENT_V1.md`, preuves v37, sélection v43 et réserve v46.

## Ce qui a été fait

La cible Modal a été préparée sans la déployer. La définition assemble vLLM et l'API dans le
même conteneur GPU tout en gardant leurs environnements Python séparés, monte les poids depuis
un volume privé et persiste l'audit dans un autre volume. Elle vérifie les checksums avant le démarrage, limite l'autoscaling à un conteneur et
revient à zéro après inactivité. Un workflow GitHub manuel et deux scénarios de smoke test
synthétiques complètent la préparation.

## Pourquoi cette étape est nécessaire

Une image locale, un notebook Kaggle ou un endpoint sur `localhost` ne prouvent pas que le
jury peut joindre l'application. Inversement, une URL HTTP 200 ne prouve ni le chargement du
bon modèle, ni l'audit, ni la sûreté clinique. La préparation sépare donc identité des poids,
service distant, authentification, persistance, smoke test et décision clinique.

## Notions à retenir

- `min_containers=0` permet le retour à zéro, mais ne fixe pas à lui seul un budget financier ;
- un volume de poids évite le téléchargement du modèle à chaque démarrage froid ;
- séparer les environnements vLLM et API évite qu'une mise à jour FastAPI/Presidio casse le runtime GPU ;
- les poids sont montés en lecture seule alors que l'audit exige un volume inscriptible ;
- le SFT v39 est le seul adaptateur servi, conformément à la sélection antérieure à la réserve ;
- le Bearer token de l'API n'est pas le token de déploiement Modal ;
- une CD manuelle et protégée reste une CD vérifiable sans déclencher des dépenses à chaque push.

## Ce qui reste ouvert

Pierre doit autoriser le fournisseur et un plafond de coût. Il faut ensuite créer les volumes
et secrets, transférer les artefacts, déployer, exécuter le smoke test, rapprocher l'audit et
observer l'extinction effective. Tant que ces actions ne sont pas réalisées, la cible reste
une implémentation locale non prouvée sur GPU Modal.
