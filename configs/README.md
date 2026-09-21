# Configurations versionnées

- Date : 2026-09-21
- Statut : `draft`
- Sources : [rapport technique](../reports/RAPPORT_TECHNIQUE_POC.md), [index des preuves](../docs/evidence/INDEX.md), scripts `scripts/build_kaggle_*.py` et `scripts/run_dpo.py`

Aucune configuration n'est supprimée : les versions historiques restent liées aux preuves qui les citent. Le statut clinique de toutes les configurations est `not_performed` ; les seuils et règles restent `proposed`.

## Configurations de la chaîne finale

| Fichier | Rôle | Preuve |
|---|---|---|
| `sft-v2.2-final-pilot.json` | Recette du SFT v2.2 exécuté par Kaggle v39 (150 étapes) | [SFT v39](../docs/evidence/SFT_V39_RESULT_2026-09-16.md) |
| `qwen3-source-sft-chat-template.jinja` | Chat template ajouté au tokenizer Base pour le SFT v39 | [relance v39](../docs/evidence/archive/SFT_V22_KAGGLE_V39_RELAUNCH_2026-09-16.md) |
| `sft-v39-handoff.json` | Identité du checkpoint SFT v39 étape 150, entrée du DPO v41, de la comparaison v43 et de la réserve v46 | [recharge v40](../docs/evidence/SFT_V40_RELOAD_RESULT_2026-09-16.md) |
| `dpo.yaml` | Recette descriptive du DPO ; ses hyperparamètres (beta 0,1, learning rate 5e-6, batch effectif 8, 20 étapes, seed 42) sont ceux du DPO v41. `scripts/run_dpo.py` code ces valeurs et ne lit pas ce fichier | [DPO v41](../docs/evidence/DPO_V41_RESULT_2026-09-16.md) |
| `final-model-selection-v43.json` | Sélection du SFT avant ouverture de la réserve (le DPO ne domine pas au sens de Pareto) | [comparaison v43](../docs/evidence/COMPARISON_V43_RESULT_2026-09-16.md) |
| `final-evaluation-frozen-v1.json` | Protocole d'évaluation finale figé le 2026-09-14 | [QA finale v35](../docs/evidence/FINAL_QA_V35_RESULT.md) |
| `stage2-safety-gates-v1.json` | Portes de sûreté proposées (ADR-016) pour le système avec garde-fous | [sûreté v36](../docs/evidence/STAGE2_SAFETY_V36_RESULT_2026-09-16.md), [vLLM v37](../docs/evidence/VLLM_V37_RESULT_2026-09-16.md) |
| `educational_triage_protocol_v1.json` | Protocole pédagogique de triage (niveaux, signaux d'alerte proposés) | [tests](../tests/test_educational_protocol.py) |
| `synthetic-schema-probe-v1.json` | Sonde de schéma sur scénarios synthétiques de développement | `scripts/build_comparison_notebook.py` |

## Configurations historiques

| Fichier | Étape |
|---|---|
| `baseline.yaml` | Baseline synthétique Qwen3 Base (2026-08-31) |
| `sft_lora.yaml` | Recette SFT/LoRA initiale (hyperparamètres `proposed`) |
| `unsloth_sft_lora.yaml` | Run technique Unsloth/MLX sur données synthétiques |
| `source_sft_5000.yaml`, `source_sft_lora.yaml`, `source_sft_lora_kaggle.yaml` | SFT source 5 000 et premier run Kaggle complet |
| `sft_authoring_queue.json` | File de rédaction des 5 000 candidats SFT |
| `sft-v2.1-pilot.json`, `sft-memorization-12.json`, `sft-resume-150-to-500.json` | Pilote SFT v2.1, test de mémorisation v21, reprise v22 |
| `sft-v22-handoff.json` | Handoff du SFT v22 (remplacé par `sft-v39-handoff.json`) |
| `final-evaluation-proposed-v1.json` | Brouillon du protocole final avant gel |
| `qa-validation-v2-expanded-v1.json` | Protocole QA élargi proposé, non exécuté |
