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
