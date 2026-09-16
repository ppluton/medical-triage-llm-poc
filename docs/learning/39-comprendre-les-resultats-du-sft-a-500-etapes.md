# Comprendre le résultat du SFT à 500 étapes

- Date : 2026-09-12
- Statut : draft
- Sources : [évaluation v22](../evidence/SFT_V22_RESULT_2026-09-12.md).

Nous avons repris le modèle général à 150 étapes et ajouté 350 étapes sur le même corpus. La restauration a fonctionné et le budget a été respecté. Les poids du test sur douze exemples n’ont pas servi à cette reprise.

Le modèle s’arrête mieux : quatre réponses sur trente atteignent le plafond, contre huit auparavant. Mais bien s’arrêter ne veut pas dire bien répondre. Sur les quinze QCM contrôlés, six ensembles de choix correspondent aux corrigés, contre sept auparavant. Une réponse qui ajoute une proposition fausse échoue même si les bonnes propositions sont présentes.

La loss continue de baisser. Elle mesure la capacité à prévoir les prochains tokens lorsqu’on fournit les morceaux précédents de la bonne réponse. En génération libre, le modèle doit aussi choisir seul ces morceaux : une erreur peut l’entraîner vers une liste répétitive ou une affirmation contraire à la référence.

Le test de mémorisation prouvait qu’il pouvait apprendre douze exercices répétés. Il ne garantissait pas la réussite sur des questions nouvelles ; le résultat actuel rappelle cette différence.

Nous avons maintenant une pipeline dont la reprise est vérifiée et un résultat de qualité mitigé. La suite proposée consiste à mesurer davantage de QCM et à classer les erreurs, avant de décider d’une nouvelle modification du modèle ou du DPO. Ce n’est ni la preuve que les sources sont mauvaises, ni la garantie qu’il suffirait d’entraîner plus longtemps.
