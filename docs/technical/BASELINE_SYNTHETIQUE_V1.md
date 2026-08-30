# Baseline synthétique v1

- **Date :** 2026-08-31
- **Statut :** observed for technical baseline; clinical references proposed
- **Sources :** `SPEC_POC_TRIAGE_MEDICAL.md`, `configs/baseline.yaml`, `data/samples/synthetic-triage-evaluation-v1.json`

Le jeu `data/samples/synthetic-triage-evaluation-v1.json` fournit huit scénarios FR/EN couvrant les catégories requises par la spécification. Les niveaux attendus et comportements sont **proposed** : ils servent à valider le pipeline technique et la comparaison base/SFT/DPO, non à mesurer une validité clinique.

Le runner `scripts/run_unsloth_mlx_baseline.py` enregistre, pour chaque scénario : version de modèle, sortie brute, sortie structurée éventuelle, latence, erreur de parsing et niveau prédit. Il utilise Qwen3 Base sans adaptateur, le template explicite `qwen3`, une génération déterministe et ne transmet jamais le niveau attendu au prompt.

Les sorties invalides restent invalides : elles ne sont ni corrigées ni converties en niveau de triage. Les métriques de triage portent uniquement sur les sorties valides, tandis que l’exact match strict divise toujours par les huit scénarios. Le run observé est consigné dans `docs/evidence/BASELINE_QWEN3_BASE_2026-08-31.md` ; son JSON complet reste hors Git sous `artifacts/`.
