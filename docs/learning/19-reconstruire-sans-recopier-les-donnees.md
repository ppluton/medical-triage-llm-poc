# Reconstruire les splits sans recopier les données médicales

- **Date :** 2026-08-31
- **Statut :** observed
- **Sources :** `docs/evidence/RECONSTRUCTION_ULTRAMEDICAL_SPLITS_2026-08-31.md`, `docs/technical/RECONSTRUCTION_ULTRAMEDICAL_SPLITS_V1.md`

## Ce qui a été fait

Nous avons produit une table de décisions pour les 112 362 lignes UltraMedical-Preference. Elle dit quelles lignes sont candidates pour l'entraînement, la validation, l'évaluation ou l'exclusion, mais elle ne copie aucun texte médical.

## Pourquoi cette approche

Une copie « nettoyée » du gigaoctet aurait créé un deuxième corpus difficile à gouverner. Un index de hashes est plus léger et plus sûr : la source reste immuable, et les étapes suivantes peuvent relire seulement les lignes retenues.

## Comment cela fonctionne

Le test a la priorité maximale. Ses prompts sont protégés. La validation vient ensuite. L'entraînement ne peut conserver que les prompts absents des deux ensembles protégés. Les préférences exactement identiques sont exclues, tandis que plusieurs préférences différentes pour le même prompt peuvent rester groupées.

## Ce que nous avons appris

- 95 350 lignes candidates ne représentent que 74 944 prompts uniques.
- Le nombre de lignes n'est donc pas le nombre de scénarios indépendants.
- Un index peut apporter la traçabilité sans multiplier les données sensibles.
- Le mot `candidate` est essentiel : la reconstruction de split n'est ni une anonymisation, ni une validation clinique.

## Prochaine étape

Construire une petite file de revue DPO liée au contrat de triage, en relisant uniquement des lignes candidates et en gardant les paires non approuvées hors entraînement. Le projet doit d'abord produire et faire valider les scénarios SFT ; le DPO vient ensuite pour apprendre des préférences de réponse sûres.
