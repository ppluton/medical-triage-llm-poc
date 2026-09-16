# Reprendre le SFT sans repartir de zéro

- Date : 2026-09-11
- Statut : draft
- Sources : [protocole de reprise](../technical/SFT_CONTINUATION_150_500_2026-09-11.md), [diagnostic de mémorisation](../evidence/SFT_MEMORIZATION_V21_RESULT_2026-09-11.md).

La v21 a montré que le modèle sait apprendre douze réponses vues. Il faut maintenant mesurer ce qu’un apprentissage supplémentaire apporte sur des questions nouvelles, en reprenant le modèle général et son corpus complet.

Une vraie reprise restaure les poids et la mémoire de l’optimiseur, la progression du learning rate et les états aléatoires. Charger seulement l’adaptateur et recommencer le scheduler constituerait une autre expérience. Nous vérifions donc l’état à 150 avant de poursuivre jusqu’à 500 étapes au maximum.

Le nombre 1 000 reste l’horizon du scheduler, pas le budget autorisé. Le programme s’arrête à 500, ou à sa limite de temps. Les anciens checkpoints sont conservés pour comparer et revenir sur une régression.

Nous ne modifions pas les sources sur une hypothèse de style non démontrée. La baisse de loss et la qualité des générations seront encore lues séparément, notamment en français et en anglais. Réussir à mémoriser n’impose pas que prolonger améliore la généralisation.
