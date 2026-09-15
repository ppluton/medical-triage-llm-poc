# Pourquoi faire apprendre seulement douze exemples ?

- Date : 2026-09-11
- Statut : draft
- Sources : [protocole](../technical/SFT_MEMORIZATION_DIAGNOSTIC_2026-09-11.md), [bilan précédent](../evidence/SFT_V20_CHECKPOINT_RESULT_2026-09-11.md).

Nous préparons un exercice volontairement facile : montrer plusieurs fois douze questions du train et leurs réponses, puis poser exactement ces questions. Cela teste une capacité de mémorisation dans la pipeline corrigée. Les réponses viennent des sources ; nous ne les réécrivons pas pour rendre le test plus facile.

La sélection privilégie des réponses courtes pour observer un résultat à petit budget. Elle ne représente donc pas les longues pages documentaires du corpus. La base et le modèle entraîné sont comparés sur les mêmes douze questions.

Si le modèle réussit, nous aurons une preuve qu’il peut apprendre ces exemples. Il faudra encore mesurer son comportement sur des questions nouvelles. S’il échoue, nous examinerons les sorties et la loss sur ce petit cas reproductible, sans conclure immédiatement que les sources sont mauvaises.

Le piège serait de présenter ce score comme une performance médicale : le modèle a précisément vu les réponses pendant l’entraînement. Les checkpoints produits servent au diagnostic, jamais à la comparaison finale ou au DPO.

## Résultat et réflexion

La v21 a terminé : **12/12 réponses reproduites exactement, espaces de bordure exclus, avec 12/12 arrêts corrects** après 25 passages sur ces douze exemples. Le modèle peut donc apprendre ce petit lot issu des trois sources. Voir le [résultat mesuré](../evidence/SFT_MEMORIZATION_V21_RESULT_2026-09-11.md).

Cela corrige notre diagnostic : une mauvaise réponse du pilote ne suffit pas à accuser le corpus ou une mécanique encore cassée. Le pilote général avait vu chaque exemple beaucoup moins souvent. Nous devons maintenant examiner un apprentissage plus long sur le corpus complet et sa généralisation, en conservant les sources tant qu’aucun défaut précis ne justifie leur modification. Ce résultat ne garantit pas qu’entraîner plus améliorera la validation.
