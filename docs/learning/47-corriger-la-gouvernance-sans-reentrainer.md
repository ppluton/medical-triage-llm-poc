# Corriger la gouvernance d'un dataset sans réentraîner

- Date : 2026-09-16
- Statut : draft
- Sources : [preuve DPO v2](../evidence/DPO_PROJECT_REVIEW_V2_2026-09-16.md), [ADR-014](../decisions/ADR-014-essai-dpo-source-filtre.md).

## Ce qui a été fait

Le lot DPO contenait des statuts de revue approuvés, mais une justification textuelle
restée à « revue en attente ». Une nouvelle version a été créée pour corriger cette
contradiction et relier explicitement le lot aux 4 700 prompts SFT protégés.

## Pourquoi c'était nécessaire

Un hash correct ne suffit pas si deux champs racontent des états incompatibles. Dans
un projet auditable, la personne qui relit doit pouvoir comprendre pourquoi une paire
est admise, qui a pris la décision et quelles limites restent ouvertes.

## Comment éviter un réentraînement inutile

Le script compare séparément le payload d'apprentissage et les métadonnées de
gouvernance. `prompt`, `chosen` et `rejected` n'ont pas changé, pas plus que les
splits, l'ordre et la provenance. Le DPO consomme ces textes ; modifier uniquement la
justification et les références de revue ne change donc pas l'exemple appris.

Le SFT est encore plus indépendant de cette correction : son checkpoint 500 est lié
par configuration aux hashes exacts du train et de la validation SFT v2.1. Relancer
un SFT aurait consommé du GPU sans tester une nouvelle hypothèse.

Le SFT et le DPO n'apprennent pas sur les mêmes types de lignes. Le premier apprend
sur les paires instruction-réponse bilingues ; le second part des poids du SFT et
apprend sur des paires de préférences UltraMedical distinctes. La cohérence vient de
la lignée des poids et de l'exclusion des prompts SFT dans le lot DPO, pas de la
réutilisation des mêmes exemples aux deux étapes.

## À retenir

- versionner une correction de gouvernance au lieu de réécrire l'artefact historique ;
- prouver quels champs sont inchangés plutôt que l'affirmer ;
- distinguer admission technique au POC et validation par un professionnel de santé ;
- ne réentraîner que lorsqu'un changement touche les données consommées, la recette,
  le modèle ou une hypothèse expérimentale utile.

La prochaine question ouverte reste la revue contextuelle de confidentialité du
corpus SFT ; elle doit produire une preuve séparée et ne sera pas transformée en
certification RGPD.
