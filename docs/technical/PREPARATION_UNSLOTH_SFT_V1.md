# Préparation Unsloth SFT v1

- **Date :** 2026-08-30
- **Statut :** observed — micro-run Core exécuté
- **Sources :** `SPEC_POC_TRIAGE_MEDICAL.md`, `CADRAGE_MISSION.md`, [guide Unsloth de fine-tuning](https://unsloth.ai/docs/get-started/fine-tuning-llms-guide)

## Périmètre et résultat observé

Cette étape prépare un format conversationnel compatible avec le *chat template* utilisé pendant le run. `scripts/prepare_sft_dataset.py` transforme uniquement des enregistrements canoniques `task_type: sft` des splits `train` ou `validation` en JSONL `messages` (`system`, `user`, `assistant`). Le split `test` provoque un échec : il reste isolé.

Le fixture `data/samples/synthetic-sft-training-v1.json` est synthétique, explicitement non revu cliniquement et ne contient aucune donnée patient. Les réponses comportent l'avertissement de sécurité contractuel. Les niveaux représentés sont des cibles de démonstration, pas des règles cliniques approuvées.

## Configuration proposée

`configs/unsloth_sft_lora.yaml` fixe le modèle prévu, la seed, un micro-run de 20 étapes et les informations qui devront être enregistrées. Les modules cibles LoRA restent `proposed_after_model_inspection` : ils devront être relevés sur la version exacte de Qwen chargée, puis reportés dans la preuve du run.

Exemple de préparation locale, avec une sortie hors Git :

```bash
.venv/bin/python scripts/prepare_sft_dataset.py \
  --input data/samples/synthetic-sft-training-v1.json \
  --output artifacts/synthetic-sft-v1.jsonl
```

Pour l'interface Unsloth, préparer les splits séparément et sélectionner le fichier de validation explicitement :

```bash
.venv/bin/python scripts/prepare_sft_dataset.py \
  --input data/samples/synthetic-sft-training-v1.json \
  --split train --output artifacts/synthetic-sft-train-v1.jsonl
.venv/bin/python scripts/prepare_sft_dataset.py \
  --input data/samples/synthetic-sft-training-v1.json \
  --split validation --output artifacts/synthetic-sft-validation-v1.jsonl
```

## Préconditions d'une exécution réelle

1. Manifeste de chaque source au statut `approved` et licence vérifiée.
2. Revue sécurité et clinique définie pour les exemples utilisés ; aucune affirmation clinique avant cette validation.
3. Distribution Unsloth et backend d'accélération explicitement choisis et testés. Le dépôt officiel propose désormais Desktop pour macOS et Core avec `uv` sur Linux/WSL ; la version exacte de Python, Unsloth, PyTorch et Transformers devra être figée dans la preuve du run.
4. Hash Git, checksum du dataset, *chat template*, hyperparamètres et emplacement hors Git des adaptateurs enregistrés.

Cette préparation prouve le contrat de préparation et l’isolement programmatique du test. Elle ne prouve ni la qualité d'un modèle, ni la sûreté clinique.

## Particularité de Qwen3 Base dans Unsloth Desktop

`unsloth/Qwen3-1.7B-Base` est un modèle Base : son tokenizer ne livre pas de *chat template*. Dans cette version de l'interface Desktop, il n'existe pas de champ pour renseigner `MLXTrainingConfig(chat_template=...)`. Le projet peut produire `--format qwen3-text`, une colonne `text` avec le template Unsloth nommé `qwen3` :

```bash
.venv/bin/python scripts/prepare_sft_dataset.py \
  --input data/samples/synthetic-sft-training-v1.json \
  --split train --format qwen3-text \
  --output artifacts/synthetic-sft-train-qwen3-v1.jsonl
```

Ce format prépare correctement les séquences complètes, prompts compris. Toutefois, l'écran de mapping de cette version Desktop n'offre que les rôles `System`, `User` et `Assistant`, et ne permet pas de sélectionner la colonne brute `text`. Il ne lève donc pas le blocage dans l'interface. Une exécution hors UI avec `MLXTrainingConfig(chat_template="qwen3")` est donc retenue afin de respecter le modèle Base exigé par le mandat.

## Exécution Core/MLX observée

Le runner `scripts/run_unsloth_mlx_sft.py` charge le snapshot local de `Qwen3-1.7B-Base`, impose `chat_template="qwen3"` au chargement et au trainer, et injecte LoRA dans les sept projections Qwen. Il exécute un pré-vol sur le manifest synthétique explicitement sélectionné avant de charger le modèle.

La fixture ne contient volontairement qu’un exemple `train`. Le runner utilise donc un batch de un et une accumulation de huit : cela évite de dupliquer artificiellement la donnée tout en gardant un batch effectif de huit. Le run observé a terminé 20 étapes ; son adaptateur, son template et `run_summary.json` sont hors Git dans `artifacts/unsloth-core-synthetic-sft-evidence/`. Les chiffres observés sont consignés dans `docs/evidence/UNSLOTH_TRAIN_PREPARATION_2026-08-30.md`.
