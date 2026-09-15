# Ce que nous apprend la comparaison v28

- Date : 2026-09-13
- Statut : draft
- Sources : docs/evidence/COMPARAISON_V28_RESULT_2026-09-13.md et JSON associé.

Nous avons enfin comparé les trois versions dans le même environnement : mêmes
questions, consigne, limite de réponse et façon de charger les poids. Les chiffres
ont été recalculés après téléchargement, sans se fier uniquement au résumé Kaggle.

Le SFT attribue une meilleure probabilité aux réponses sources que la Base.
Le DPO change très peu ce résultat et ne rend pas le triage plus fiable dans ce
run. Une erreur d'apprentissage faible et un fichier de poids valide ne suffisent
pas : les réponses de triage répètent du texte, inventent des informations et ne
terminent souvent pas le JSON. Ces échecs doivent apparaître dans le rapport.

Un autre point est visible : le même SFT donnait davantage de JSON valides avec
Unsloth dans v26. V28 utilise Transformers avec une quantification FP4 explicite.
Nous n'avons pas encore isolé quelle différence explique ce recul. Ce serait donc
prématuré de conclure que le corpus est de nouveau cassé, ou qu'un entraînement
plus long résoudrait le problème. Le prochain contrôle doit être petit et porter
sur l'inférence du même checkpoint, avant toute nouvelle décision d'entraînement.

Le test réservé reste inutilisé afin de ne pas régler le modèle sur son examen
final. Ces observations sont techniques et pédagogiques ; elles ne constituent
pas une validation clinique.
