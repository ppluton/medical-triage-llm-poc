# Pourquoi une évaluation a bloqué l'entraînement

- **Date :** 2026-09-11
- **Statut :** draft
- **Sources :** [constat v18](../evidence/SFT_V2_PILOT_V18_2026-09-11.md), [contrat AMP CPU](../evidence/SFT_FP16_CPU_CONTRACT_2026-09-11.json), [lancement v19](../evidence/SFT_V2_PILOT_V19_LAUNCH_2026-09-11.json), sources Unsloth 2026.8.22 et Transformers 5.5.0 inspectées.

## Ce qui a été fait et pourquoi

Le pilote v18 a terminé son évaluation de départ, puis échoué à la première mise à jour. Les données avaient passé leurs contrôles, mais cela ne prouvait pas que le passage évaluation → entraînement conservait les bonnes propriétés numériques.

L'inspection du trainer généré par Kaggle a révélé qu'Unsloth activait automatiquement `fp16_full_eval`. Lors d'une évaluation exécutée avant l'entraînement, Transformers utilise ce réglage pour convertir le modèle en FP16. Cette conversion touche aussi les paramètres LoRA entraînables.

## Comprendre FP16 et FP32

FP16 utilise 16 bits par nombre ; FP32 en utilise 32. Le premier réduit la mémoire et peut accélérer les calculs, mais représente moins de valeurs et avec moins de précision. Un entraînement en précision mixte combine plusieurs formats : certaines opérations en FP16, des paramètres entraînables et leurs gradients en FP32.

Le mécanisme AMP ajuste l'échelle des gradients pour limiter les problèmes numériques. Dans le chemin utilisé ici, il refuse de traiter les gradients stockés en FP16. D'où le message `Attempting to unscale FP16 gradients.` Ce n'est ni une question médicale mal rédigée ni une loss trop élevée : c'est une incompatibilité dans l'état numérique attendu par l'optimiseur.

## La correction et sa vérification

Nous désactivons la conversion complète d'évaluation **après** l'initialisation du trainer, car son constructeur modifie les réglages. Nous contrôlons ensuite que les 392 tenseurs entraînables restent en FP32 avant l'évaluation, après la loss, après la génération et après l'entraînement. La base reste quantifiée et les calculs conservent leur précision mixte.

Un petit modèle linéaire CPU reproduit exactement l'erreur lorsqu'il subit la conversion en FP16. Sans cette conversion, la mise à jour est finie et modifie ses poids. Ce contrôle explique le mécanisme ; il ne remplace pas le test GPU.

La version 19 commence donc par deux étapes sur T4, puis recharge le checkpoint dans un nouveau processus. Elle compare les générations avant/après recharge, vérifie la restauration des étapes de l'optimiseur et poursuit jusqu'à quatre étapes. Le pilote borné ne démarre que si ces contrôles réussissent.

## Ce qui reste distinct

- Une mise à jour sans erreur ne prouve pas que les réponses s'améliorent.
- Une recharge d'adaptateur ne prouve pas à elle seule une reprise complète d'entraînement.
- Une reprise jusqu'à quatre étapes ne prouve pas encore l'égalité bit à bit avec quatre étapes continues sur GPU.
- Le corpus, l'apprentissage, la génération et la validation clinique conservent chacun leurs contrôles et leurs limites.

Les résultats mesurés de v19 doivent être lus dans les preuves d'exécution, pas déduits du seul protocole décrit ici.
