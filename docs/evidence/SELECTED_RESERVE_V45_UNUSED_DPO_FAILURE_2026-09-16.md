# Échec de dépendance DPO inutilisée — réserve v45

- Date : 2026-09-16
- Statut : `failed_before_model_load`
- Notebook privé : `pierrepluton/chsa-source-sft-qwen3`, version 45
- Log SHA-256 : `a14992593482d77589050cbed85eb37aac0bdbb7c56f5aa3387329e1042aa71d`
- Optimisation : 0 étape
- Sorties de modèle sur la réserve : 0

## Cause

Le contrôle du manifeste de réserve corrigé passe, ainsi que le checksum du snapshot Base.
Le runner appelle ensuite `verify_completed_dpo` bien que la décision finale sélectionne SFT.
Le dataset DPO privé contient `WEIGHT_CHECKS.json` à sa racine, mais le bootstrap n’a copié que
la politique et `RUN_SUMMARY.json` vers `/kaggle/working/selected-dpo-v41`. La vérification
échoue donc sur l’absence de `weight_checks.json` avant chargement du modèle.

## Décision de correction

Le candidat DPO n’a aucune raison d’être monté ou vérifié pendant l’évaluation finale du SFT.
Le runner rend désormais `--dpo-run` optionnel et ne le demande que si la décision sélectionne
explicitement `dpo`. Pour SFT, il enregistre que DPO n’a pas été chargé. Le builder n’attache
que les datasets Base et SFT ; la lignée DPO reste prouvée par la comparaison v43 et son
fichier de décision, sans dépendance GPU inutile.

Comme v45 n’a produit aucune génération ou métrique de réserve, cette correction technique ne
change ni sélection, ni modèle, ni prompt, ni garde-fou. Une reprise v46 reste admissible et
doit être documentée comme telle.
