# Diagnostic de mémorisation SFT sur douze exemples train

- Date : 2026-09-11
- Statut : draft — protocole exécuté en v21, objectif de mémorisation atteint
- Sources : `configs/sft-memorization-12.json`, résultats v19/v20, corpus v2.1-reviewed et runner `scripts/run_source_sft_pilot.py`.

## Question et portée

Après correction des transformations et du défaut FP16, la génération reste insuffisante. Tester si le modèle peut apprendre douze réponses connues permet de distinguer une capacité d’apprentissage sur exemples vus d’une généralisation encore incertaine. Aucun nouvel exemple médical ni label clinique n’est rédigé.

La sélection prend quatre exemples de chaque source dans le train, dont la réponse compte 1 à 128 tokens, triés par SHA-256 de `memorization-42:record_id`. Elle est indépendante des réponses générées sur validation. Les empreintes des fichiers parents et du tokenizer sont vérifiées. Le jeu source et ses splits restent inchangés.

## Exécution prévue

Base Qwen3-1.7B figée et LoRA neuf ; mêmes cibles, rang et précision que v19. Douze exemples seulement, batch 1, accumulation 1, learning rate 2e-4, warmup 5, scheduler linéaire sur 300 étapes. Arrêt à 300 étapes ou 900 secondes de phase d’entraînement. Installation, baseline et génération finale s’ajoutent ; timeout du sous-processus 2 400 secondes.

Les douze réponses sont générées avant/après en greedy, cap 256 tokens, EOS natif. La loss est mesurée sur ces mêmes douze exemples : c’est explicitement une mesure **sur train**, pas une validation. Validation et test ne sont pas utilisés pour calculer un résultat ni pour mettre à jour les poids. Le paquet existant contient le fichier validation pour vérifier l’intégrité du parent ; le mode diagnostic le remplace en mémoire par le lot train avant tout calcul modèle.

Cible technique fixée avant exécution : 12/12 réponses textuellement identiques après normalisation et 12/12 EOS. Un résultat inférieur reste partiel/inconclusif ; ce seuil n’est pas clinique. Une réussite ne prouve pas l’apprentissage de toutes les formes longues, la généralisation ni le triage.

Les checkpoints du pilote général sont copiés et préservés avant le diagnostic. Les nouveaux poids sont enregistrés sous `train-memorization-12` et ne doivent jamais devenir le SFT final ou la base DPO.

## Preuves avant lancement

Neuf tests ciblés passent : sélection train uniquement, refus des identifiants exclus/inconnus, doublons et cohortes incomplètes, budgets et synthèse des métriques. Ruff passe. Le préflight du paquet doit réussir avant publication dans le notebook privé existant, uniquement T4 gratuite. Aucun SFT long n’est lancé par ce protocole.

## Résultat

Le [bilan v21](../evidence/SFT_MEMORIZATION_V21_RESULT_2026-09-11.md) établit 12/12 réponses exactes et terminées après 300 étapes. Les validations locales complètes comptent 118 tests réussis. La généralisation reste non mesurée dans ce diagnostic.
