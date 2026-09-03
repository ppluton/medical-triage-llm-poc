# Distinguer expérimentation technique et validation clinique

- **Date :** 2026-09-03
- **Statut :** draft
- **Sources :** ADR-007, protocole expérimental v1, règles de preuve du dépôt

## Ce qui a été décidé

Le manque de médecin ne bloque plus l'entraînement scolaire. Le projet utilisera des cibles synthétiques proposées par un protocole versionné, tout en maintenant la revue clinique à `pending`.

## Pourquoi cette distinction est importante

Un POC peut répondre à la question « peut-on construire et exécuter cette chaîne technique ? » sans répondre à la question « cette chaîne est-elle sûre pour de vrais patients ? ». Confondre ces deux questions conduit soit à bloquer inutilement le projet, soit à produire une affirmation médicale injustifiée.

## Ce que l'AI Engineer peut démontrer

- provenance et licence des sources ;
- reproductibilité de la génération ;
- isolation des splits ;
- fonctionnement SFT et DPO ;
- conformité des sorties au schéma ;
- métriques sur les références expérimentales ;
- latence, consommation mémoire et traçabilité ;
- limites et cas d'échec observés.

## Ce qu'il ne peut pas conclure seul

- que les priorités sont médicalement correctes ;
- que le taux de sous-triage est acceptable en pratique ;
- que l'outil est conforme comme dispositif médical ;
- que le CHSA pourrait le mettre en production ;
- que l'anonymisation technique constitue un avis juridique RGPD.

## Formulation à employer à l'oral

« J'ai construit un protocole expérimental reproductible pour créer et comparer Base, SFT et DPO. Les labels sont des références internes au POC, pas des décisions cliniques validées. Mon résultat porte sur la faisabilité technique et identifie explicitement la validation clinique comme étape future. »

## Étape suivante

Implémenter le générateur des 5 000 enregistrements canoniques, vérifier la diversité et les fuites, figer les splits, puis préparer les fichiers SFT sans encore lancer le run complet.
