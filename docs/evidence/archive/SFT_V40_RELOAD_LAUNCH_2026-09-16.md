# Lancement de la vérification de recharge SFT — Kaggle v40

- Date : 2026-09-16
- Statut observé : `COMPLETE`
- Notebook privé : `pierrepluton/chsa-source-sft-qwen3`, version 40
- Mode : read_only_pilot_reload
- Étapes d'optimisation prévues : 0
- Notebook SHA-256 : `20b11fb9540be2d3c4326c21a54ee90145543815262a913fe66b4dab4b774ba8`

La v40 attache la sortie réussie v39 et exige l'unique résumé portant le SHA-256
`41a7e0c8e54154bac44f4bb6a21e3fe5a5b80a97523409b86a359f1f7b7972b2`.
Elle recopie l'archive avant vérification, recharge le checkpoint 150 dans un nouveau
processus, compare les trente générations greedy et la NLL, puis évalue les checkpoints
50 et 100. Aucun entraînement et aucun test final ne sont autorisés par ce paquet.

Le statut `RUNNING` prouvait uniquement le lancement. La v40 est ensuite passée à
`COMPLETE` ; ses sorties téléchargées et vérifiées sont décrites dans
[le résultat v40](../SFT_V40_RELOAD_RESULT_2026-09-16.md).
