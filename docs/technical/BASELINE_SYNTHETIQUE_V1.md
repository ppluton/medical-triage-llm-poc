# Baseline synthétique v1

Le jeu `data/samples/synthetic-triage-evaluation-v1.json` fournit huit scénarios FR/EN couvrant les catégories requises par la spécification. Les niveaux attendus et comportements sont **proposed** : ils servent à valider le pipeline technique et la comparaison base/SFT/DPO, non à mesurer une validité clinique.

La baseline devra enregistrer, pour chaque scénario : version de modèle, prompt, sortie brute, sortie structurée, latence, erreur éventuelle et métriques calculées. Une fois Qwen disponible, les résultats seront ajoutés dans `docs/evidence/` sans écraser ce jeu de référence.
