# Lire le pilote sans confondre loss, format et qualité

- **Date :** 2026-09-11
- **Statut :** draft
- **Sources :** [résultats du pilote v19](../evidence/SFT_V19_PILOT_RESULT_2026-09-11.md), [revue textuelle](../evidence/SFT_V19_OUTPUT_REVIEW_2026-09-11.json), [volume des tokens supervisés](../evidence/SFT_SUPERVISED_TOKEN_VOLUME_2026-09-11.json).

## Ce qui a été fait

Après correction du défaut FP16, nous avons effectué un pilote de 150 étapes depuis la base. Il a terminé et produit une sauvegarde complète. Nous avons ensuite confronté la baisse de loss aux réponses générées, au lieu de considérer l'entraînement terminé comme une preuve de qualité.

## Pourquoi les trois lectures sont nécessaires

La **loss** s'améliore nettement : 1,4569 avant apprentissage, 0,7121 après le pilote sur les mêmes références. Le modèle prédit donc mieux les tokens attendus lorsqu'il reçoit les tokens précédents de la bonne réponse. Cela n'assure pas qu'il choisira cette réponse lorsqu'il génère seul.

Le **format** progresse en français : les 15 réponses s'arrêtent avant le plafond. Mais recopier toutes les propositions d'un QCM donne une sortie propre et finie tout en répondant faux à la question.

L'**accord aux réponses sources** doit alors être mesuré séparément. Le comptage textuel strict passe de 0 à 7. Or la base avait déjà cinq réponses dont le choix correspondait à la référence, avec une introduction ou une explication. La revue des ensembles de choix donne donc 5 → 7, avec quatre gains et deux régressions. Présenter 0 → 7 comme une amélioration d'exactitude aurait exagéré le résultat.

Cette revue est une comparaison textuelle assistée, pas une validation clinique. Elle ne certifie pas l'exactitude médicale actuelle des références.

## Le total peut masquer des sous-ensembles différents

Le nombre total de réponses terminées progresse de 20 à 22 sur 30. En français, il passe de 11 à 15. En anglais, il baisse de 9 à 7. Il faut donc lire les deux sous-ensembles, même si le total paraît meilleur.

Les réponses anglaises montrent encore des boucles, des listes générées artificiellement et des contradictions avec les références. Trois références dépassent elles-mêmes 512 tokens ; cela explique pourquoi un plafond atteint ne suffit pas à conclure à une boucle. La lecture des textes confirme toutefois plusieurs répétitions manifestes indépendamment de cette limite.

## Compter les lignes ne suffit pas à décrire le corpus

Dans le train revu, MedQuAD représente 1 746 lignes sur 3 721, soit moins de la moitié. Mais ses réponses représentent 408 644 tokens supervisés sur 455 471, soit environ **89,7 % du volume des réponses**. Les QCM français sont beaucoup plus courts.

Les 291 réponses contenant un format HPO standardisé représentent à elles seules 129 281 tokens, soit environ **28,4 % du volume total des réponses train**. Le modèle est donc très exposé à cette forme documentaire.

Ces mesures décrivent le corpus ; elles ne mesurent pas directement la contribution de chaque source au gradient et ne prouvent pas que les paragraphes standardisés causent les boucles. Une modification de pondération ou de nettoyage devrait faire l'objet d'une comparaison contrôlée, avec validation inchangée et test toujours réservé.

## Ce que signifie « données propres » ici

Nous avons vérifié la provenance, les transformations, les choix des QCM, l'isolation selon des clés définies et les labels reçus par le trainer. Ces preuves restent valables. Elles ne rendent pas automatiquement chaque réponse idéale pour apprendre le style d'un assistant et ne certifient pas sa vérité clinique.

Il faut distinguer :

1. Un exemple mal transformé : erreur de préparation à corriger.
2. Une réponse source fidèle mais très standardisée ou peu adaptée à une réponse directe : choix de corpus à examiner.
3. Une réponse générée qui contredit sa référence : erreur du modèle, pas preuve à elle seule que la référence a été mal préparée.
4. Une référence médicale périmée ou contestable : revue clinique distincte, non réalisée par ces tests logiciels.

## La décision suivante

Le pilote n'est pas perdu : son checkpoint permet une reprise, et les checkpoints 50 et 100 permettent de vérifier si la meilleure loss correspond aussi aux meilleures réponses. La v20 a terminé cette comparaison : 26/30 réponses terminées à 50 étapes, 25/30 à 100 et 22/30 à 150. Pourtant, certaines réponses précoces ne font que répéter la question. Aucun de ces checkpoints ne suffit donc à conclure que le modèle est prêt. La recharge à 150 reproduit exactement les 30 réponses : ce défaut qualitatif ne vient pas d’une sauvegarde défectueuse. Nous ne changeons ni la sélection d'évaluation ni les références pour améliorer artificiellement les scores.

La mécanique GPU fonctionne dans le périmètre testé. Le niveau de qualité souhaité pour une démonstration reste une décision séparée, fondée sur les sorties et leurs limites. Aucun résultat de ce pilote n'autorise un usage clinique autonome.
