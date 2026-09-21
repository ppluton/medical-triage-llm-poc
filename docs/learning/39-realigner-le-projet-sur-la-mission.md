# Revenir au problème demandé plutôt qu'accumuler les essais

- Date : 2026-09-12
- Statut : draft
- Source : [audit de la mission et des livrables](../evidence/AUDIT_ALIGNEMENT_MISSION_2026-09-12.md).

Nous avons relu toute la page de mission, ses quatre étapes dépliées et la soutenance dans le navigateur Codex. Cela permet de distinguer les consignes de l'école de nos propres choix techniques.

La mission demande bien un petit modèle Base, SFT/LoRA puis DPO. Il n'y a donc pas lieu de changer de modèle uniquement parce que les réponses déçoivent. En revanche, nous avons commis des erreurs de préparation : enlever des propositions d'un QCM revient à donner à l'élève une question dont une partie de l'énoncé manque. Couper le corrigé ou ne pas enseigner correctement la fin de réponse ajoute encore de la confusion. Ces défauts étaient les nôtres et leur correction était nécessaire.

Après réparation, nous avons continué à regarder essentiellement un petit contrôle de connaissances. Or le projet doit aussi montrer un assistant qui demande des précisions, produit une priorité et laisse une trace. Un QCM aide à observer la spécialisation médicale ; il ne remplace pas la démonstration de ce parcours. La baisse de loss signifie que les textes de référence deviennent plus prévisibles, pas que chaque réponse libre devient juste.

Autre raccourci à corriger : DPO compare deux réponses au même contexte pour favoriser la réponse préférée. Il n'apprend pas automatiquement la prudence ou les niveaux de triage si les préférences ne portent pas sur ces comportements. Il faut regarder ce que contiennent les paires et mesurer ce qui change.

Le projet ne repart pas de zéro. Le corpus revu, les sauvegardes, les mesures et les composants API restent utiles. Il faut maintenant relier ces pièces, fixer une évaluation adaptée à la mission et terminer les livrables. Le raccord DPO contient encore une référence à l'ancien modèle : c'est une tâche concrète, contrairement à l'objectif impossible « être certain que tout fonctionnera » avant toute expérience.

L'école demande bien une démarche de validation clinique ; il faut clarifier avec le mentor quelle preuve est attendue dans ce scénario scolaire. En attendant, nous pouvons documenter les expériences techniques et les références proposées sans inventer une approbation. Un résultat négatif doit être expliqué, mais il ne remplace pas les livrables techniques demandés.
