# ADR-012 — Isoler les groupes documentaires avant le pilote SFT

- Date : 2026-09-11
- Statut : proposed
- Propriétaire : porteur du POC
- Statut clinique : not validated
- Sources : ADR-008, corpus v2 figé, audit préalable du 11 septembre, demande utilisateur de vérifier avant relance.

## Contexte

L'absence de questions identiques ne garantit pas l'indépendance documentaire. L'inventaire v2 trouve 145 documents MedQuAD répartis sur plusieurs splits. Les micro-runs ne testent pas la reprise de l'optimiseur et du scheduler.

## Décision proposée et implémentation locale de contrôle

Conserver v2 et tous ses résultats. Préparer un candidat v2.1 par exclusions uniquement, sans réaffecter de ligne : les groupes contenant du test restent réservés au test, puis priorité à validation sur train. Grouper par document MedQuAD, réponse MedQuAD identique normalisée, question source identique et vignette MediQAl identique non vide. Appliquer la fermeture transitive des groupes. Aucun contenu de test n'est généré ni revu pour mesurer la performance ; seuls les identifiants, métadonnées et empreintes servent à l'isolation.

Conserver les exclusions et hashes ; accepter un corpus légèrement inférieur à 5 000 plutôt que remplir les quotas avec des données non auditées. Les comptages finaux doivent être mesurés. Aucun ancien checkpoint SFT ne doit être présenté comme entraîné avec cette isolation.

Le futur pilote repart de la base épinglée, utilise la loss sur réponse seule, un jeu de validation figé et un budget GPU borné. Il doit conserver optimiseur, scheduler, RNG, état du trainer et adaptateur. Une reprise nécessite le même horizon de scheduler ; prolonger arbitrairement un scheduler déjà terminé n'est pas une reprise équivalente.

## Alternatives et conséquences

Garder les splits v2 conserve les quotas mais expose au recouvrement documentaire. Déplacer les données d'évaluation dans train invaliderait l'historique. Une nouvelle collecte serait plus coûteuse. L'exclusion est conservatrice et traçable, mais réduit les effectifs et ne prouve pas l'absence de paraphrases ou la qualité clinique.

Aucun entraînement n'est autorisé automatiquement par ces contrôles. Présenter les résultats et expliquer le pilote à l'utilisateur avant son lancement, conformément à sa demande.
