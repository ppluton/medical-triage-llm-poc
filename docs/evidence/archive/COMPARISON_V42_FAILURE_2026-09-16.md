# Échec de préparation runtime de la comparaison v42

- Date : 2026-09-16
- Statut : failed_before_model_load
- Notebook privé : `pierrepluton/chsa-source-sft-qwen3`, version 42
- Optimisation et évaluations exécutées : 0

Le paquet a installé ses dépendances puis le runner a échoué à l'import de `api.py` avec
`ModuleNotFoundError: No module named 'triage_poc.collection'`. Le builder embarquait
`api.py` mais avait omis ce module local. Aucun modèle n'a été chargé, aucune validation
n'a été évaluée et la réserve finale était absente du paquet.

La correction v43 ajoute uniquement `collection.py`. Le builder analyse désormais les
AST de tous les fichiers Python embarqués et refuse toute importation `triage_poc.*` dont
le module n'est pas présent. L'avertissement pip sur une dépendance optionnelle de
`google-adk` n'est pas la cause de l'échec.
