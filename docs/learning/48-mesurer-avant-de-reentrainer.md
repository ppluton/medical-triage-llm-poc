# Mesurer la sûreté avant de réentraîner

- Date : 2026-09-16
- Statut : draft
- Sources : [évaluation v36](../evidence/STAGE2_SAFETY_V36_RESULT_2026-09-16.md), [ADR-016](../decisions/ADR-016-portes-surete-etape-2.md).

## Ce qui a été fait

Les mêmes 18 scénarios ont été rapprochés des sorties Base, SFT et DPO. Une file
aveugle a permis de lire 54 réponses sans connaître leur variante, puis un évaluateur
a combiné la revue textuelle aux mesures automatiques.

## Pourquoi cette étape précède un nouvel entraînement

Une loss plus faible ne dit pas pourquoi une sortie échoue. Le modèle peut connaître
du vocabulaire médical tout en inventant une constante, confondre « non renseigné »
avec « absent », produire un texte tronqué ou choisir une priorité inadéquate. Ajouter
des étapes d'entraînement sans distinguer ces causes rendrait le résultat impossible à
interpréter.

La comparaison montre aussi qu'un défaut peut être partagé par SFT et DPO, tandis que
la Base réussit parfois un contrôle critique. Cela oriente d'abord vers la chaîne de
prompt, d'anonymisation, de décodage et de garde-fous. Le DPO n'est pas une garantie
de vérité ; ses préférences biomédicales ne ciblent pas directement ces comportements.

## À retenir

- un schéma JSON valide ne garantit pas un contenu fondé ;
- `unknown`, `absent` et `normal` sont trois états différents ;
- les sorties doivent être revues sans connaître le modèle lorsque c'est possible ;
- un jeu de développement vu reste utile pour la régression, pas pour une conclusion
  finale aveugle ;
- on ne réentraîne qu'après avoir formulé une hypothèse testable sur la cause.

La prochaine itération est donc locale et déterministe. Un nouveau run GPU ne sera
justifié que si les mêmes erreurs subsistent après ces corrections.
