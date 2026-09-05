# API de démonstration avec fournisseur de modèle privé

- **Date :** 2026-09-05
- **Statut :** draft — contrat testé, vLLM réel non encore vérifié
- **Sources :** spécification, ADR-010, `api.py`, `serving.py`, `tests/test_serving.py`.

## Entrées, sorties et limites

`POST /v1/triage` valide FR/EN, groupe d'âge, symptômes non vides, durée, antécédents, allergies, traitements et constantes. Les champs inconnus et valeurs non finies sont refusés par le contrat. Le fournisseur accepte les noms de constantes `temperature_c`, `heart_rate`, `respiratory_rate`, `spo2`, `systolic_bp`, `diastolic_bp` ; aucune limite clinique numérique n'est inventée.

La sortie contient priorité, synthèse, rationale, informations manquantes, questions complémentaires, signaux d'alerte, identifiant, version, durée et avertissement FR/EN. Le fournisseur demande à un endpoint compatible `/v1/chat/completions` une réponse conforme au schéma. Il refuse les générations tronquées et les JSON invalides.

Presidio FR/EN analyse les champs textuels avant transmission. Si une analyse échoue ou laisse des identifiants détectés, aucun appel au modèle n'est effectué. Les faux positifs NER restent une limite fonctionnelle à évaluer sur les scénarios médicaux : une anonymisation technique ne garantit pas la préservation sémantique.

Le prompt demande l'escalade professionnelle et des questions complémentaires quand le contexte est incomplet ou contradictoire. Cette demande n'est pas une politique de triage validée ni un garde-fou clinique déterministe. Les tests ne prouvent ni l'adaptation des questions réelles ni la sûreté des priorités.

## Configuration locale privée

La factory `triage_poc.serving:create_serving_app` nécessite :

- `TRIAGE_API_TOKEN` : secret local d'au moins 32 caractères ; jamais versionné ;
- `TRIAGE_VLLM_URL` : racine API finissant par `/v1`, HTTPS hors localhost ou réseau de démonstration `vllm` ;
- `TRIAGE_MODEL_NAME` : nom exact exposé par le serveur ;
- `TRIAGE_MODEL_VERSION` : révision/checksum de l'artefact servi ;
- `TRIAGE_AUDIT_PATH` : fichier hors Git accessible à l'utilisateur du processus.

```bash
# À démarrer et gérer via Portly si le serveur doit persister.
uvicorn triage_poc.serving:create_serving_app --factory \
  --host 127.0.0.1 --port 8000 --no-access-log
```

Toute route de cette factory, y compris docs et health, exige `Authorization: Bearer ...`. Le module `triage_poc.api:app` conserve un mode sans fournisseur : health disponible, triage 503. Son statut health ne prouve pas la disponibilité du modèle.

## Audit

Le journal JSONL contient identifiant, date UTC, langue, version modèle/prompt/contrôles, statut et latence. Il ne contient ni contexte, ni réponse, ni secret. Un nouveau fichier est créé avec permissions 0600. Si l'écriture échoue, l'API ne délivre pas l'évaluation. Le brief demande un audit clinique plus riche ; le contenu et la rétention de cet audit restent à valider selon ADR-010.

## Docker et CI

L'image contient l'API, les dépendances exportées de `uv.lock` et les modèles spaCy `fr_core_news_md` et `en_core_web_sm` 3.8.0. Les poids Qwen, les données et les dépendances d'entraînement GPU en sont exclus. Le paquet est installé sans ses dépendances globales, car le serveur d'inférence est séparé ; l'image n'est donc pas un environnement baseline ou SFT.

```bash
uv export --frozen --no-dev --no-emit-project --prune torch --prune transformers \
  --no-hashes --no-annotate --output-file requirements/api.txt
docker build -t medical-triage-poc:post-sft-local .
```

L'image tourne sous UID 10001. Préparer les permissions du volume d'audit avant l'utilisation de la factory. La CI ajoutée construit l'image et exerce le contrat sans modèle ; aucune étape de publication ou de déploiement distant n'est activée.

## Preuves attendues encore distinctes

Tests locaux et smoke du conteneur, appel au vrai modèle vLLM, anonymisation sur cas de démonstration, erreurs et latence p50/p95 sous charge, revue médicale, accès privé déployé. Un résultat de l'un de ces niveaux ne remplace pas les autres.
