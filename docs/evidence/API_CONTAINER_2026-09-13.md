# Construction et contrat du conteneur API

- Date : 2026-09-13
- Statut : draft — conteneur local vérifié sans modèle
- Sources : Dockerfile, journal `val_f625e4ace9f1`, commande Docker locale.

Checkout `codex/complete-poc-evaluation`, code au commit `1f5693b`.
Docker Desktop Linux aarch64 ; image `chsa-api:1f5693b` construite avec code 0.
Image config : `sha256:b5508a8bdb161acde2d0cc500936f9554ae1219508ea6c5a436f9adeb447c784`.
La réservation de build est terminée et la place libérée.

La première réservation `val_a8c6006b671e` a échoué car le PATH du processus ne
contenait pas `docker-credential-osxkeychain`. La reprise ajoute explicitement
`/Applications/Docker.app/Contents/Resources/bin` au PATH du build ; aucun
identifiant ni paramètre de compte n'a été changé. Les couches de dépendances
existantes ont été réutilisées : ce n'est pas une reconstruction sans cache.

Un conteneur éphémère `--rm --network none` a ensuite exécuté TestClient :
`GET /healthz` retourne 200 et `POST /v1/triage` avec un contexte synthétique
retourne 503 lorsque le fournisseur manque. Code 0, sortie
`container contract passed; model absent`. Le conteneur est supprimé à sa sortie.

Cela vérifie le packaging API et son refus de produire une évaluation sans modèle.
Cela ne prouve ni l'inférence vLLM, ni un service HTTP exposé, ni l'architecture
Linux amd64 distante, ni les performances ou la qualité du triage.
