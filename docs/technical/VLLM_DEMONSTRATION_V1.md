# Préparation de la démonstration vLLM

- Date : 2026-09-13
- Statut : proposed — recette à vérifier sur GPU, aucun serveur lancé
- Sources : manifeste `configs/sft-v22-handoff.json`, contrôle DPO v27, `serving.py`, documentation officielle [LoRA vLLM](https://docs.vllm.ai/en/v0.15.0/features/lora/) et [serveur compatible](https://docs.vllm.ai/en/v0.15.0/serving/openai_compatible_server/).

## Identité et séparation des preuves

Le modèle de base est `unsloth/Qwen3-1.7B-Base`, révision
`e249956c10337100486d07afb77e3eb2b30906b8`.
Le SFT porte l'empreinte `5c195a8c83bfd6493e7ffd74ec20e3d97207f9b650850aabd8de25afffea626d`.
Le DPO porte l'empreinte `6eda116c8bec89596c83beb09342094758db23abed5fa3391330965713ec85fd`.
Le choix final du modèle reste ouvert en attendant v28.

vLLM peut charger l'adaptateur LoRA au-dessus du modèle de base : une fusion et
un nouvel entraînement ne sont pas des prérequis de cette recette. Le serveur
doit utiliser le tokenizer archivé du SFT et son template de conversation, ainsi
que le nom de modèle demandé par l'API. Ne pas substituer un modèle Instruct.

La première expérience proposée utilise FP16 avec LoRA rang 16, contexte 2048,
une séquence à la fois et exécution eager. Cette précision diffère de la
comparaison 4 bits v28 : les réponses et la latence du service doivent donc être
mesurées séparément, sans prétendre à une équivalence numérique.

## Recette candidate de lancement

Dans un environnement GPU isolé avec vLLM 0.15.0, après vérification des artefacts,
`SFT_ADAPTER` et `SELECTED_ADAPTER` désignent leurs chemins absolus existants :

```bash
vllm serve unsloth/Qwen3-1.7B-Base \
  --revision e249956c10337100486d07afb77e3eb2b30906b8 \
  --tokenizer "$SFT_ADAPTER" \
  --chat-template "$SFT_ADAPTER/chat_template.jinja" \
  --dtype half --max-model-len 2048 --max-num-seqs 1 \
  --enforce-eager --enable-lora --max-lora-rank 16 \
  --lora-modules "chsa-selected=$SELECTED_ADAPTER" \
  --host 127.0.0.1 --port 8001
```

Les dépendances CUDA/Torch de cette version doivent être vérifiées dans cet
environnement avant de figer la recette. Ne pas installer vLLM dans le runtime
DPO ou interrompre v28. L'écoute locale seule est intentionnelle pour la preuve
d'intégration ; elle ne constitue pas l'endpoint cloud accessible du mandat.

## Vérifications décisives

1. Vérifier les fichiers puis le modèle annoncé par `/v1/models`.
2. Comparer le rendu des messages avec le tokenizer archivé, en conservant EOS natif et prompt v3.
3. Appeler réellement `/v1/chat/completions`, avec le schéma attendu par `VllmProvider` ; conserver les erreurs et raisons de terminaison.
4. Démarrer la factory API authentifiée avec URL locale `/v1`, nom `chsa-selected`, version contenant le checksum et fichier d'audit privé.
5. Exécuter les scénarios synthétiques via `evaluate_triage_endpoint.py` et rapprocher l'audit avec `verify_endpoint_audit.py`.
6. Vérifier après redémarrage la disponibilité du même adaptateur et la conservation des traces ; mesurer séparément démarrage et régime établi.

Le schéma JSON contraint du service peut améliorer la conformité de format : ce
résultat doit être distingué des sorties libres de v28 et de la pertinence du triage.
La cible cloud, l'accès privé, le budget, la rétention et le déploiement CI/CD
restent à concrétiser. Aucune publication externe n'est autorisée par cette recette.

## Composition Docker préparée

`compose.demo.yaml` décrit vLLM et la factory API. Renseigner localement
`SFT_ADAPTER`, `SELECTED_ADAPTER`, `TRIAGE_MODEL_VERSION`, `TRIAGE_API_TOKEN`
et `TRIAGE_AUDIT_DIRECTORY`. Les chemins doivent exister ; le montage ne crée pas
silencieusement un dossier vide. Le répertoire d'audit doit être privé et accessible
à l'UID 10001 de l'image API. Ne pas changer les droits d'un dossier partagé.

Les deux adaptateurs sont montés en lecture seule. Aucun port vLLM n'est publié
sur l'hôte ; seul le port API 8000 est lié à 127.0.0.1. Le réseau Docker relie les
deux services. Le premier démarrage doit télécharger le modèle de base : cette
composition nécessite Linux, NVIDIA Container Toolkit, Internet et un GPU autorisé.
Le tag vLLM est fixé à 0.15.0 ; disponibilité de l'image et compatibilité matérielle
restent à vérifier avant le démarrage, puis consigner son digest réel.

Validation effectuée : `docker compose -f compose.demo.yaml config --quiet`
avec chemins et token synthétiques, sortie 0. Cela prouve uniquement la validité
de la configuration Compose. Aucun conteneur n'a été construit ni lancé dans
cette étape. Le démarrage du modèle peut être plus long que celui de l'API : un
health API ne suffit pas ; attendre et réussir une inférence avant la démonstration.
Un accès cloud et une procédure CI/CD restent des étapes distinctes.
