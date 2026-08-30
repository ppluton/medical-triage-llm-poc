# Premier pas avec Unsloth pour le SFT

- **Date :** 2026-08-30
- **Statut :** observed
- **Sources :** `CADRAGE_MISSION.md`, `SPEC_POC_TRIAGE_MEDICAL.md`, [guide Unsloth de fine-tuning](https://unsloth.ai/docs/get-started/fine-tuning-llms-guide)

## Ce qui a été fait

Nous avons ajouté une passerelle entre le contrat de données de triage et le format de conversations attendu par un entraînement SFT avec Unsloth. Chaque exemple devient une conversation avec : une règle de rôle, un contexte patient structuré et une réponse JSON structurée.

## Pourquoi c’était nécessaire

Un notebook de fine-tuning est un moteur, mais il ne décide ni du format des données, ni de leur provenance, ni de ce qui peut servir à évaluer le modèle. Sans cette passerelle, il est facile de mélanger le jeu de test aux données d’apprentissage ou de perdre l’avertissement de sécurité dans la réponse cible.

## Comment cela fonctionne

Le script valide d’abord chaque enregistrement contre le schéma versionné. Il refuse un autre type de tâche que `sft`, les doublons et le split `test`. Il sérialise ensuite le contexte et la sortie sans reformuler de contenu médical. Qwen3 Base ne fournit pas lui-même de *chat template* : le runner Unsloth Core choisit explicitement `qwen3` au chargement et dans le trainer, puis ce template est conservé avec l’adaptateur.

## À retenir

- Un entraînement SFT apprend à imiter une réponse cible ; il ne valide pas que cette réponse est vraie ou sûre.
- Le jeu `test` reste séparé pour mesurer un comportement qui n'a pas servi à ajuster le modèle.
- Des scénarios synthétiques permettent de vérifier le pipeline sans faire croire à une validation clinique.
- Unsloth Core/MLX a permis un micro-run de 20 étapes sur Apple Silicon ; l’interface Desktop beta ne permettait pas ce même réglage avec Qwen3 Base.
- Unsloth peut rendre le fine-tuning plus accessible, mais ne remplace ni gouvernance des données ni évaluation de sûreté.

## Hypothèses et questions ouvertes

Le micro-run Core est une preuve de faisabilité technique, non une configuration définitive. Il reste à exécuter une baseline sur des sources approuvées, obtenir la revue clinique des cibles d’entraînement, puis comparer SFT et DPO avec un protocole stable et un jeu test isolé.
