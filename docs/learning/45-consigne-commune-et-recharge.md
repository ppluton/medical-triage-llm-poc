# Séparer le modèle, sa recharge et la consigne

- Date : 2026-09-12
- Statut : draft
- Sources : [résultat v25](../evidence/TRIAGE_V25_RESULT_2026-09-12.md), [consigne partagée](../../src/triage_poc/triage_prompt.py).

Nous avons vérifié deux questions différentes : est-ce le bon modèle qui répond,
et sait-il réaliser le triage demandé ? Le cache Unsloth gardait des copies anciennes
malgré le chargement correct des poids. Le vider a permis de reproduire trente
réponses à l'identique. Réparer cette recharge ne rend pas ces réponses meilleures.

L'évaluation de triage donne ensuite seulement quatre priorités conformes sur dix-huit
scénarios. Mais nous demandions des catégories sans expliquer précisément leur sens.
C'est comme évaluer une copie avec un barème que l'élève n'a pas reçu. Nous avons donc
rendu explicite le protocole pédagogique déjà proposé, dans une consigne commune à
l'API et à l'évaluation. Elle distingue notamment « information inconnue » et « absence
confirmée », afin de ne pas encourager des faits inventés.

Les contrôles locaux peuvent prouver que cette consigne arrive au fournisseur et que
la référence attendue n'y apparaît pas. Ils ne prouvent pas que le modèle la suit.
Il reste à mesurer cet effet sur GPU, puis à comparer le DPO dans les mêmes conditions.
Les catégories restent pédagogiques, sans approbation clinique. Les résultats v25
sont conservés : changer la consigne ne permet pas de réécrire une mesure passée.

## Ce que la mesure v26 nous apprend

La consigne explicite améliore le format (12/18 au lieu de 10/18) et les priorités
conformes aux références proposées (6/18 au lieu de 4/18). Elle ne résout pas les
faits inventés ni les erreurs de priorité. Un cas reçoit même la bonne priorité en
inventant des antécédents : compter uniquement les catégories masquerait ce défaut.
La suite doit donc conserver des évaluations de fidélité et de sûreté, en plus du format.

## Comparer les trois modèles avec la même règle de mesure

La comparaison après DPO doit refaire aussi les mesures Base et SFT. Sinon une
bibliothèque ou une quantification différente pourrait expliquer un écart attribué
à tort au DPO. Le nouveau runner garde les mêmes entrées, la même consigne, le même
tokenizer et les mêmes budgets pour les trois variantes. Le test final reste réservé.
Sa préparation locale ne vaut pas encore résultat GPU : les résultats v26 restent
présentés séparément jusqu'à cette mesure commune.

Le contrôle de préparation a aussi évité une comparaison incorrecte : le template
sauvegardé contient le marqueur de fin historique, tandis que le SFT transforme
explicitement sa dernière fin de réponse en EOS natif. Réutiliser le helper ancien
pour calculer la loss aurait évalué une autre cible. Le nouveau runner reprend donc
exactement le rendu du SFT. Les 479 références passent ce contrôle avant lancement.
