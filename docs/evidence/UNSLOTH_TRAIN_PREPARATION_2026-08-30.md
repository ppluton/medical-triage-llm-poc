# Micro-run SFT synthétique avec Unsloth Core/MLX

- **Date :** 2026-08-30
- **Statut :** observed — micro-run Core terminé ; Desktop limité par son interface
- **Sources :** `configs/unsloth_sft_lora.yaml`, `data/samples/synthetic-sft-training-v1.json`, `src/triage_poc/training_preflight.py`

## Question et périmètre

Vérifier un micro-run SFT purement synthétique sur Qwen3 Base, sans donnée patient, et documenter la limite constatée de l’interface Desktop.

## Entrées, environnement et configuration

- Modèle sélectionné : `unsloth/Qwen3-1.7B-Base`.
- Hardware affiché : Apple M4, 24 GiB.
- Datasets importés localement : JSONL synthétiques distincts pour `train` et `validation`, sans split `test`.
- Configuration affichée : LoRA 16-bit, 20 étapes, batch 2 × accumulation 4, contexte 2048, learning rate `0.0002`, token Hugging Face non configuré.

L’interface a accepté l’import et a affiché l’état `Ready`. Les deux sorties explicites du script sont aussi disponibles hors Git : une ligne `train` et une ligne `validation`.

## Résultat et limite

Le pré-vol versionné a ensuite été réalisé sur le seul manifeste synthétique `src-synthetic-sft-fixture.json`, approuvé pour une vérification technique (et non clinique). Le bouton Unsloth `Start Training` a été actionné. Le run a échoué à l’étape 0, sans checkpoint ni métrique : `unsloth/Qwen3-1.7B-Base` est un modèle Base dont le tokenizer ne contient pas de `chat_template`.

Le message d’Unsloth indique deux correctifs possibles : renseigner `MLXTrainingConfig(chat_template=...)`, indisponible dans les réglages Desktop exposés ici, ou fournir une colonne `text` pré-rendue. Le projet produit un format `qwen3-text` déterministe avec les marqueurs du template Unsloth `qwen3`; les fichiers restent séparés par split. Lors du nouveau lancement, Desktop a bien lu la colonne `text`, mais son écran de mapping n’offre que les rôles `System`, `User` et `Assistant` — aucun rôle de texte complet. Il n’est donc pas possible de confirmer cette voie dans cette version de l’onglet Train.

Unsloth Core/MLX a ensuite été installé dans un environnement local isolé et a chargé le snapshot local Qwen3 Base, appliqué la quantification 4-bit MLX et injecté LoRA (17 432 576 paramètres entraînables, 3,18 % du total). Le `chat_template="qwen3"` a été accepté. Le premier appel Core s’est arrêté avant la première étape car le fixture `train` ne comporte qu’un exemple et le batch configuré valait deux. Le script Core adapte donc ce micro-run à un batch de un et une accumulation de huit, sans duplication de donnée, avant une nouvelle tentative.

La seconde tentative Core a terminé les 20 étapes et enregistré les adaptateurs dans `artifacts/unsloth-core-synthetic-sft-evidence/` (hors Git), avec un `run_summary.json`. Mesures observées : `train_loss=1.7539518636067708`, durée `93.83842291700421 s`, 6 000 tokens traités et pic mémoire MLX `2.319369968 GiB`. Le fichier `adapters.safetensors` pèse environ 67 Mo. Ces valeurs viennent d’un seul exemple d’entraînement synthétique et d’un seul exemple de validation ; elles ne sont pas une métrique de qualité.

## Ce que cela prouve et ne prouve pas

**Prouvé :** Unsloth Core/MLX charge le snapshot local Qwen3 Base, applique LoRA, utilise explicitement le template `qwen3`, termine 20 étapes et enregistre un adaptateur LoRA local. Unsloth Desktop charge les données et le modèle, mais son interface bloque la voie `messages` automatique pour ce modèle Base.

**Non prouvé :** amélioration générale, métrique de validation significative, comportement de triage, sûreté ou validation clinique. Ce micro-run est une preuve d’exécution technique, pas une évaluation du modèle.

## Étape suivante

Le chemin autorisé pour un micro-run purement synthétique est formalisé dans `docs/decisions/ADR-002-micro-run-sft-synthetique-isole.md`. Prochaine étape : exécuter la baseline puis le SFT sur des sources approuvées et des splits substantiels, en gardant le même protocole et un jeu test isolé.
