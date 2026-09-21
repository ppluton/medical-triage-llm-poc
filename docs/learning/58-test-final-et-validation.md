# Pourquoi garder une évaluation finale à part

- Date : 2026-09-13
- Statut : draft
- Sources : docs/technical/EVALUATION_FINALE_PROPOSEE_V1.md, règles du projet sur les splits.

Nous avons préparé un protocole pour les 500 exemples réservés, sans ouvrir leurs
réponses. La validation sert à comparer les essais et à prendre des décisions.
Le test sert ensuite à mesurer le résultat de ces décisions sur des exemples
qui ne les ont pas guidées. Changer le modèle après avoir vu son résultat au test
retire à ce test son indépendance.

La proposition calcule l'erreur sur les 500 exemples et limite les générations
à 50 identifiants sélectionnés de façon déterministe, avant les résultats.
Cela borne le coût GPU sans choisir les questions où le modèle semble réussir.
Ce sous-ensemble peut être déséquilibré : sa composition devra être montrée.

Ce travail est une préparation, pas une mesure. Il reste à figer les modèles et
le runtime après v28 et à adapter le runner. Les QCM et réponses documentaires
ne deviennent pas des exemples de priorité de triage ; la démonstration API et
la validation clinique restent des questions distinctes.

L'exporteur final partage maintenant le format des messages du SFT. Son entrée
est explicitement réservée à l'évaluation : le code d'entraînement refuse toujours
ces lignes. Les contrôles utilisent uniquement des données synthétiques et
vérifient que les exemples train ne passent pas dans l'export final. Le corpus
réservé réel n'a pas encore été exporté ni évalué.
