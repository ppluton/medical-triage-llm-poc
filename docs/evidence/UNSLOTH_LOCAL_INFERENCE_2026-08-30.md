# Vérification locale Unsloth — chargement d'inférence

- **Date :** 2026-08-30
- **Statut :** observed — génération brute locale réussie
- **Sources :** Unsloth Desktop `0.1.804-beta`, CLI `unsloth 2026.8.22`, `configs/unsloth_sft_lora.yaml`

## Question et périmètre

Vérifier qu’Unsloth peut sélectionner et commencer à charger localement le modèle `unsloth/Qwen3-1.7B-Base` sur le Mac Apple Silicon de développement. Aucun dataset, prompt médical, entraînement, compte Hugging Face ou endpoint réseau n’est inclus.

## Environnement et commande

- Matériel détecté par Unsloth : Apple M4, 24 GiB de mémoire unifiée.
- Backend détecté : MLX / Apple Silicon (`arm64`).
- Modèle présent dans le cache local : `unsloth/Qwen3-1.7B-Base`, snapshot `e249956c10337100486d07afb77e3eb2b30906b8`.

```bash
unsloth inference unsloth/Qwen3-1.7B-Base \
  'Reply with exactly one word: READY' \
  --temperature 0 --max-new-tokens 4 --no-think --no-server --verbose
```

## Résultats observés

Le CLI a sélectionné MLX, créé un sous-processus d’inférence et journalisé le chargement de `unsloth/Qwen3-1.7B-Base` via `mlx-lm`. Il a annoncé une limite mémoire MLX de 16,21 Go. L’interface Desktop a ensuite confirmé « loaded successfully » pour le même modèle.

Une complétion brute, sans template de chat, a été exécutée avec le runtime MLX fourni par Unsloth :

```bash
~/.unsloth/studio/unsloth_studio/bin/python -m mlx_lm.generate \
  --model ~/.cache/huggingface/hub/models--unsloth--Qwen3-1.7B-Base/snapshots/e249956c10337100486d07afb77e3eb2b30906b8 \
  --prompt 'The answer is' --ignore-chat-template --max-tokens 4 --temp 0 --verbose False
```

La sortie observée était `100`.

Le test de l’interface Chat, avec le prompt neutre `Reply with exactly one word: READY`, a échoué avant génération. Le log local identifie la cause : `tokenizer.chat_template is not set`. C’est cohérent avec l’usage d’un modèle `Base`, qui n’est pas livré comme un modèle conversationnel prêt à l’emploi.

## Ce que cela prouve et ne prouve pas

**Prouvé :** le modèle est accessible dans Unsloth, le chemin de chargement local MLX démarre sur cette machine et une complétion brute locale produit une sortie.

**Non prouvé :** une génération conversationnelle par l’interface Chat avec ce modèle Base ; elle exige un template explicite ou un modèle Instruct. Cette vérification ne porte pas sur le triage, la qualité, la sûreté, la latence ni une validation clinique.

## Étape suivante

Définir et versionner le template de chat qui sera employé pendant le SFT et l’inférence, puis vérifier une conversation non médicale. Seulement ensuite, tester les scénarios synthétiques d’évaluation isolés.
