# Geler l'évaluation avant de regarder

- Date : 2026-09-16
- Statut : draft
- Source : [preuve de gel](../evidence/TRIAGE_RESERVE_V1_FREEZE_2026-09-16.md)

## Pourquoi créer une nouvelle réserve

Un scénario déjà utilisé pour corriger un prompt ou un garde-fou devient une donnée de
développement. Même si le modèle n'a pas été entraîné dessus, nos décisions ont appris de
ses résultats. Le rejouer reste utile pour la régression mais ne mesure plus honnêtement la
généralisation finale.

## Ce qui a été fait

Une nouvelle réserve synthétique FR/EN a été écrite et gelée avant la fin du SFT v2.2. Son
hash, sa composition et son absence de recouvrement exact avec le développement sont
enregistrés. Les références restent explicitement proposées car aucun clinicien ne les a
validées.

## À retenir

- l'isolation temporelle compte autant que l'isolation des identifiants ;
- regarder les résultats puis modifier le système consomme le caractère final du test ;
- un test de triage synthétique ne remplace pas le test QA réservé du corpus ;
- une référence proposée mesure le protocole du POC, pas une vérité clinique certifiée ;
- un checksum permet de prouver que le jeu n'a pas changé après sa création.
