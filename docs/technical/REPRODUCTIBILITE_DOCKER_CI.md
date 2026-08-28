# Reproductibilité locale — Docker et CI

- **Statut :** implemented; image not built locally

`Dockerfile` installe le paquet et expose l'API FastAPI sur le port 8000. L'absence de fournisseur de modèle retourne volontairement `503` : un démarrage de conteneur ne prouve donc pas une inférence.

Le workflow GitHub Actions exécute les tests, Ruff et la lecture des contrats JSON. Il ne télécharge aucune donnée médicale, n'entraîne aucun modèle et ne déploie rien.

## Preuve et limite

Les commandes locales Python ont déjà validé 11 tests et Ruff. Le build Docker et une exécution GitHub Actions restent non prouvés localement : Docker/GitHub ne sont pas invoqués dans cette étape.
