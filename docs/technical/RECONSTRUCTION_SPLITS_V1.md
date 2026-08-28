# Reconstruction des splits v1

Les splits natifs FrenchMedMCQA ont une fuite textuelle. `split_rebuild.py` attribue donc un split déterministe à chaque groupe de question normalisée : 70 % train, 15 % validation, 15 % test. Toutes les variantes textuellement normalisées d'une question restent dans le même split.

Cette règle corrige les doublons exacts normalisés, pas les paraphrases ou la fuite sémantique. Le résultat dérivé reste hors Git et `candidate` jusqu'aux contrôles PII et revue requis.
