# Reproductibilité locale — Docker et CI

- **Statut :** implemented; local container checks passed

`Dockerfile` installe le paquet et expose l'API FastAPI sur le port 8000. L'absence de fournisseur de modèle retourne volontairement `503` : un démarrage de conteneur ne prouve donc pas une inférence.

Le workflow GitHub Actions exécute les tests, Ruff et la lecture des contrats JSON. Le
job conteneur vérifie deux modes hors réseau : le refus `503` sans fournisseur, puis le
démarrage de la factory privée avec configuration synthétique, refus `401` sans token et
health authentifié indiquant explicitement `clinical_validation=not_performed`. Aucun de
ces contrôles n'appelle vLLM. Le workflow ne télécharge aucune donnée médicale,
n'entraîne aucun modèle et ne déploie rien.

## Preuve et limite

Les tests Python et Ruff sont validés localement. Le 16 septembre 2026, le build Docker
et les deux sondes hors réseau ont aussi réussi dans le job local
`val_0b32860bf240`. Cela ne prouve pas l'exécution future du workflow GitHub Actions,
le démarrage vLLM, l'inférence GPU ou un déploiement cloud.
