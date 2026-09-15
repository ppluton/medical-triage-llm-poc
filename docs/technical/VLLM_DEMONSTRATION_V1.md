# Préparation de la démonstration vLLM

- Date : 2026-09-13
- Statut : proposed — recette GPU en cours de vérification, API non prouvée
- Sources : manifeste `configs/sft-v22-handoff.json`, contrôle DPO v27, `serving.py`, documentation officielle [LoRA vLLM](https://docs.vllm.ai/en/v0.15.0/features/lora/) et [serveur compatible](https://docs.vllm.ai/en/v0.15.0/serving/openai_compatible_server/).

## Identité et séparation des preuves

Le modèle de base est `unsloth/Qwen3-1.7B-Base`, révision
`e249956c10337100486d07afb77e3eb2b30906b8`.
Le SFT porte l'empreinte `5c195a8c83bfd6493e7ffd74ec20e3d97207f9b650850aabd8de25afffea626d`.
Le DPO porte l'empreinte `6eda116c8bec89596c83beb09342094758db23abed5fa3391330965713ec85fd`.
La comparaison v28 est terminée sans gain de triage démontré ; le choix final
reste ouvert jusqu’aux mesures de la chaîne vLLM/API.

vLLM peut charger l'adaptateur LoRA au-dessus du modèle de base : une fusion et
un nouvel entraînement ne sont pas des prérequis de cette recette. Le serveur
doit utiliser le tokenizer archivé du SFT et son template de conversation, ainsi
que le nom de modèle demandé par l'API. Ne pas substituer un modèle Instruct.

La première expérience proposée utilise FP16 avec LoRA rang 16, contexte 4096,
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
  --dtype half --max-model-len 4096 --max-num-seqs 1 \
  --enforce-eager --enable-lora --max-lora-rank 16 \
  --lora-modules "chsa-selected=$SELECTED_ADAPTER" \
  --host 127.0.0.1 --port 8001
```

Les dépendances CUDA/Torch de cette version doivent être vérifiées dans cet
environnement avant de figer la recette. Ne pas installer vLLM dans le runtime
DPO. L'écoute locale seule est intentionnelle pour la preuve
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
Le manifeste du registre confirme le tag 0.15.0 pour Linux amd64 et arm64.
La composition fixe Linux amd64 et le digest
`sha256:97187c9535fd6d6040444d68bb073f17344fd454e9241cc7a4e998141f244543`.
Preuve : `docs/evidence/VLLM_IMAGE_MANIFEST_2026-09-13.json`.
Le téléchargement de l'image et la compatibilité GPU restent à vérifier.

Validation effectuée : `docker compose -f compose.demo.yaml config --quiet`
avec chemins et token synthétiques, sortie 0. Cela prouve uniquement la validité
de la configuration Compose. Aucun conteneur n'a été construit ni lancé dans
cette étape. Le démarrage du modèle peut être plus long que celui de l'API : un
health API ne suffit pas ; attendre et réussir une inférence avant la démonstration.
Un accès cloud et une procédure CI/CD restent des étapes distinctes.

## Candidat de comparaison API Base/SFT/DPO — 14 septembre

Statut au 14 septembre : draft, préparé localement, alors non lancé. La recette utilise désormais le contexte
4096 mesuré en v34. Le runner inclut la Base sans adaptateur, puis SFT et DPO,
avec le même serveur, tokenizer SFT, prompt, schéma et lot de 18 scénarios. Le nom
servi de la Base a été vérifié dans `models.json` de v34. L'ordre est consigné ;
les latences restent influencées par l'échauffement et les caches.

Le builder exige un nom de sortie explicite pour éviter d'appeler « v34 » un nouvel
essai utilisant du code différent :

```sh
python scripts/build_kaggle_vllm_demo.py \
  --metadata artifacts/kaggle/vllm-api-v34-final/kernel-metadata.json \
  --output artifacts/kaggle/api-collection-candidate-2 \
  --run-name api-collection-candidate-2
```

Cette commande crée un dossier neuf et ne publie rien. Le candidat comprend
l'API 0.3.0 et son suivi de collecte, prompt v5. Les 39 fichiers embarqués ont été
comparés au checkout et les sources Python compilées sans exécution ; Ruff et
`docker compose -f compose.demo.yaml config -q` passent avec des paramètres
synthétiques. Empreinte du notebook candidat :
`d3f82158863c8bb5985bb799c441b8eefe4d537457f18813cc7c2a69a9b12870`.

Ces contrôles établissent la cohérence du paquet, pas son fonctionnement GPU.
Le lot courant mesure un appel par scénario ; une preuve du parcours complet
sur plusieurs appels avec le modèle réel reste à ajouter. Le candidat ne remplace
pas l'évaluation QA v35 alors figée en cours.

Le candidat précédent est remplacé par `artifacts/kaggle/api-dialogue-candidate`
(nom de run `api-dialogue-candidate`), qui inclut les deux dialogues FR/EN et la
synchronisation d'audit. Voir la [préparation et ses limites](../evidence/DIALOGUE_DRIVER_LOCAL_2026-09-14.md).
Le notebook SHA-256 est `3f5a79ec62eebfca17a6e1e726b08d145e95b6424f7e996bc8d1c19a40b3e2ff`.
Il a ensuite été exécuté sous le nom v36 ; ses résultats sont décrits dans la section
suivante et dans la preuve de sûreté dédiée.

## Candidat v37 après revue de sûreté — 16 septembre

Le run v36 a finalement été exécuté puis revu ; ses sorties restent la preuve historique de
l'API 0.3.0 et du prompt v5. La revue a révélé des faits non étayés, des signaux d'alerte
omis et des textes corrompus. L'API 0.4.0 candidate ajoute une anonymisation de service plus
ciblée, le prompt v6 et `proposed-guardrails-v1`. Le
[replay hors ligne](../evidence/STAGE2_GUARDRAIL_REPLAY_V36_2026-09-16.md) montre la logique
sur les sorties sauvegardées, sans relancer les modèles.

Le paquet `api-guardrails-v37` est maintenant [préparé et vérifié
localement](../evidence/VLLM_V37_PACKAGE_2026-09-16.md). Il embarque les sources exactes de
l'API 0.4.0, conserve Base, SFT et DPO inchangés, vérifie la version des garde-fous dans
l'audit et résume `model_output`, `corrected` et `safe_fallback` par variante. Tant que ce
paquet n'est pas exécuté, le prompt v6 et la chaîne complète restent non prouvés sur GPU.
Ce run est une régression d'inférence, pas un nouvel entraînement.
