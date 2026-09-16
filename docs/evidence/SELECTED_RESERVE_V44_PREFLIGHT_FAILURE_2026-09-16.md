# Échec de préflight de la réserve v44

- Date : 2026-09-16
- Statut : `failed_before_model_load`
- Notebook privé : `pierrepluton/chsa-source-sft-qwen3`, version 44
- Log SHA-256 : `ddf5307161380580c3ed108d4adc89d6bfb9b40177895b3e8611b519bdc58b73`
- Optimisation : 0 étape
- Sorties de modèle sur la réserve : 0

## Cause

`validate_frozen_reserve` reconstruisait correctement le manifeste, puis comparait l’objet
JSON complet. Les deux champs `path` différaient nécessairement entre le dépôt local et le
dossier embarqué `/kaggle/working/...`, tandis que les SHA-256, effectifs, distributions,
statuts et contrôles d’isolation étaient identiques. Le garde-fou a donc levé
`The held-out reserve differs from its frozen manifest` à 33 secondes.

## Portée

Le script a lu les fichiers de réserve et de développement pour recalculer leurs invariants,
mais a échoué avant `verify_base_snapshot`, avant chargement du modèle et avant toute
génération. Aucune réponse de réserve, métrique de modèle ou décision post-réserve n’a été
observée. La sélection SFT v39 reste donc inchangée.

## Correction ciblée

La comparaison ignore désormais uniquement la chaîne d’emplacement `path` pour les sections
`artifact` et `development_reference`. Tous les invariants de contenu restent comparés à
l’identique : hash, nombre de lignes, catégories, langues, niveaux proposés, isolation,
statut et limites. Un test reproduit le même contenu via des chemins absolus et passe avec les
tests de gel existants.

Une reprise technique peut être lancée parce que v44 n’a produit aucune observation de modèle.
Elle sera présentée comme v45, pas comme une première ouverture réussie.
