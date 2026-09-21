# Fermer le corpus sans inventer une certification RGPD

- Date : 2026-09-16
- Statut : draft
- Sources : [preuve v2.2](../evidence/SFT_PRIVACY_FINALIZATION_2026-09-16.md),
  [processus RGPD](../governance/PROCESSUS_RGPD_CORPUS_V1.md).

## Ce qui a été fait

Nous avons transformé les 31 alertes de nom explicite en remplacements vérifiables, sans
modifier silencieusement le corpus déjà utilisé. Une nouvelle version v2.2 porte ses propres
hashes, son schéma, sa révision de code et un journal de décision sans texte médical.

## Pourquoi cette solution

Masquer un nom explicite est une précaution proportionnée. Masquer toutes les entités
`PERSON`, `LOCATION` et `DATE_TIME` ne l'est pas : ces catégories contiennent aussi des
auteurs, maladies, structures anatomiques et durées utiles. Le projet retient donc ces
alertes contextuelles seulement dans son périmètre de sources publiques et d'entraînement
local contrôlé, tout en bloquant la publication externe.

## À retenir

- un checksum vérifié avant transformation empêche de corriger le mauvais corpus ;
- des positions exactes rendent chaque remplacement reproductible ;
- toute modification textuelle crée une nouvelle version et impose un rescan ;
- « prêt pour un POC local » ne veut pas dire « anonyme au sens juridique » ;
- un statut honnête et borné permet d'avancer sans masquer une limite réelle.
