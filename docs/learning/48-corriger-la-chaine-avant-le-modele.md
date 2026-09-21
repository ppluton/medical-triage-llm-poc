# Corriger la chaîne avant de réentraîner le modèle

- Date : 2026-09-16
- Statut : draft
- Sources : [garde-fous v1](../technical/GARDE_FOUS_DETERMINISTES_V1.md),
  [replay v36](../evidence/STAGE2_GUARDRAIL_REPLAY_V36_2026-09-16.md).

## Ce qui a été fait

Les défauts observés en v36 ont été transformés en contrôles explicites et testables. La
chaîne distingue maintenant une sortie inchangée, une correction déterministe et un
remplacement conservateur. Elle journalise aussi la version et les raisons de cette décision.

L'anonymisation de l'API a été séparée de celle du corpus. Pour le corpus, une détection large
reste utile afin de préparer une revue. Pour une interaction de triage, masquer toutes les
dates et tous les lieux peut supprimer une durée ou un contexte clinique utile. La politique
de service cible donc les identifiants à haute précision et échoue fermé en cas de problème.

## Pourquoi c'est différent d'un nouveau SFT

Un SFT modifie une distribution probabiliste ; il ne garantit pas qu'une phrase interdite ne
sortira jamais. Ici, les invariants les plus importants sont placés après le modèle et testés
comme du code. Cela permet de corriger rapidement les causes certaines — mauvaise politique
PII, priorité minimale, texte tronqué — sans attribuer à tort chaque défaut aux poids.

Le replay montre toutefois la limite : remplacer 8 à 11 réponses sur 18 signifie que les
garde-fous contiennent le risque visible, mais que le modèle reste trop souvent inutilisable.
Les garde-fous ne doivent donc pas devenir un maquillage statistique.

## À retenir

- un modèle génératif peut inventer un fait même après SFT et DPO ;
- une contrainte JSON contrôle la forme, pas la vérité ;
- les invariants de sûreté mesurables appartiennent aussi au code de service ;
- toute correction automatique doit être versionnée et visible dans l'audit ;
- un taux de fallback élevé est une métrique de dette modèle/données ;
- un replay historique valide une logique, pas le comportement d'un nouveau runtime GPU.

La prochaine expérience doit tester une seule hypothèse : est-ce que la chaîne v37 exécute
ces contrôles de bout en bout avec les mêmes modèles ? Ce résultat guidera ensuite une
éventuelle modification ciblée des données ou de l'entraînement.
