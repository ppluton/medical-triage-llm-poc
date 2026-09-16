# Pourquoi refaire le SFT sans promettre un meilleur modèle

- Date : 2026-09-16
- Statut : draft
- Sources : [revue v37](../evidence/STAGE2_SAFETY_V37_BLIND_REVIEW_2026-09-16.md),
  [ADR-017](../decisions/ADR-017-reentrainer-sur-corpus-final-v2-2.md).

## Ce qui a été appris

Une revue aveugle peut montrer que deux modèles ont les mêmes types de défauts sans prouver
qu'ils sont identiques. Ici, SFT et DPO ont chacun 6 sorties signalées sur les 17 comparables,
avec les mêmes comptes par catégorie. Cela ne démontre pas un bénéfice DPO.

## Pourquoi refaire malgré tout

La raison principale n'est pas le score : c'est la lignée. Le modèle livré doit être relié
au corpus final, à ses splits, à sa confidentialité et à ses hashes. Un checkpoint entraîné
sur une version antérieure ne satisfait pas cette exigence, même s'il fonctionne techniquement.

## À retenir

- reproductibilité du livrable et amélioration de qualité sont deux questions différentes ;
- le nouveau SFT corrige la première et devra mesurer la seconde ;
- l'absence de gain DPO est un résultat utile, pas une raison de cacher ou rallonger le run ;
- un jeu déjà vu guide l'itération mais ne devient pas un test final ;
- aucun entraînement ne transforme une revue de projet en validation clinique.
