# Baseline synthétique Qwen3 Base

- **Date :** 2026-08-31
- **Statut :** observed — échec du contrat JSON sur les huit scénarios
- **Sources :** `configs/baseline.yaml`, `data/samples/synthetic-triage-evaluation-v1.json`, `scripts/run_unsloth_mlx_baseline.py`

## Question et claim testé

Vérifier si `unsloth/Qwen3-1.7B-Base`, sans adaptateur, peut produire localement une réponse JSON conforme au contrat minimal de triage sur les huit scénarios synthétiques proposés.

Le contrat minimal exige `triage_level`, `summary`, `missing_information` et `safety_notice`. Le niveau doit être exactement `maximum`, `moderate` ou `deferred`. Les niveaux attendus ne sont pas inclus dans les prompts.

## Environnement et commande

- Apple M4, 24 GiB de mémoire unifiée ; backend MLX.
- Python `3.13.14`, Unsloth `2026.8.22`.
- Snapshot local Qwen3 Base `e249956c10337100486d07afb77e3eb2b30906b8`.
- Quantification MLX 4-bit, template `qwen3`, génération déterministe, maximum 384 nouveaux tokens.

```bash
PYTHONPATH=src .unsloth-core/bin/python scripts/run_unsloth_mlx_baseline.py \
  --model-path <snapshot-local-qwen3-base> \
  --scenarios data/samples/synthetic-triage-evaluation-v1.json \
  --output artifacts/baseline-qwen3-base-synthetic-v1.json \
  --max-new-tokens 384
```

## Résultats observés

- Scénarios exécutés : 8/8.
- Sorties JSON valides : 0/8.
- Sorties invalides : 8/8.
- Exact match strict : `0.0`.
- Latence moyenne : `18 179.525 ms` ; minimum `4 318.0 ms` ; maximum `24 550.2 ms`.
- Sept sorties contiennent un objet JSON incomplet et répétitif, principalement sous la forme `//{`.
- Une sortie contient une structure sémantiquement proche du contrat, mais chaque ligne est commentée avec `//` ; elle reste donc invalide.
- Artefact brut hors Git : `artifacts/baseline-qwen3-base-synthetic-v1.json`, SHA-256 `d0e18314f5fee9f0a6bb599187354a8e670b23e6a36b9cd4d71af114d87a78a7`.

## Ce que cela prouve et ne prouve pas

**Prouvé :** le pipeline charge Qwen3 Base, exécute les huit prompts et détecte sans correction silencieuse que le modèle Base ne respecte pas encore le contrat JSON. Cette baseline fournit un point de comparaison reproductible pour un futur checkpoint SFT.

**Non prouvé :** les références synthétiques ne sont pas validées cliniquement. Le résultat ne mesure donc ni pertinence clinique, ni sûreté, ni aptitude au déploiement. Il ne prouve pas non plus qu’un dataset SFT plus grand améliorera nécessairement le modèle.

## Décision suivante

Conserver cette baseline inchangée. La prochaine comparaison devra exécuter le même runner, les mêmes scénarios et le même parsing sur un checkpoint SFT gouverné, sans utiliser ces résultats pour modifier le jeu test.
