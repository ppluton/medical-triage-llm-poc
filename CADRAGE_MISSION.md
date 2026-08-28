# Cadrage de mission — POC Agent IA de triage médical

## Contexte

Le Centre Hospitalier Saint-Aurélien (CHSA), grand hôpital public français, fait face à une surcharge constante des urgences, particulièrement aux heures de pointe. Le manque ponctuel de personnel de triage allonge l’attente et accroît le risque que des cas critiques soient identifiés tardivement.

## Commanditaire et mandat

**Dr. Marie Dubois — Directrice Innovation Médicale, CHSA**

La Direction du CHSA mandate un·e IA Engineer junior pour réaliser, en quatre semaines, un Proof of Concept (POC) d’agent IA de triage médical. Le mandat consiste à démontrer la faisabilité technique et la valeur ajoutée clinique potentielle d’un assistant de triage initial.

## Problème et objectif

Le CHSA veut assister — sans remplacer — le personnel soignant lors de la première évaluation des patients. Le POC doit montrer qu’un agent spécialisé peut :

- collecter les symptômes via un questionnaire intelligent et adaptatif ;
- évaluer une priorité : `urgence maximale`, `urgence modérée` ou `prise en charge différée`, conformément à des protocoles établis ;
- fournir une explication claire de l’évaluation et des recommandations ;
- être intégrable au système d’information hospitalier ;
- garantir une trace exploitable de chaque interaction pour les audits médicaux.

## Limites de responsabilité

Ce projet est un POC d’assistance. Il ne constitue ni un dispositif médical en exploitation, ni un outil de diagnostic, de prescription ou de décision clinique autonome. Toute décision reste de la responsabilité des professionnels de santé. Les seuils d’acceptation et la validation clinique doivent être fixés par le CHSA.

## Stratégie expérimentale

1. **Validation conceptuelle** — déployer **Qwen3-1.7B-Base**, modèle compact, pour tester la faisabilité, la qualité des échanges et l’acceptabilité clinique.
2. **Optimisation ciblée** — réaliser un fine-tuning supervisé (SFT) avec LoRA, puis un alignement par préférences avec DPO afin d’améliorer la conformité aux pratiques cliniques.
3. **Projection industrielle** — si le POC est concluant, étudier des modèles de 32B+ paramètres et des données étendues pour une trajectoire de production.

## Feuille de route sur quatre semaines

| Semaine | Objectif | Résultats attendus |
|---|---|---|
| 1 | Agréger MediQA, FrenchMedMCQA, MedQuAD et UltraMedical-Preference ; nettoyer, anonymiser et versionner les données | Dataset bilingue, ~5 000 paires SFT, paires DPO, splits train/validation/test, schéma de métadonnées et justification RGPD |
| 2 | Spécialiser Qwen3-1.7B-Base par SFT + LoRA | Checkpoints reproductibles, logs, hyperparamètres, métriques intermédiaires |
| 3 | Aligner le modèle à l’aide de DPO | Comparaison SFT/DPO, contrôles d’hallucinations et de recommandations dangereuses |
| 4 | Déployer et valider le POC | Endpoint vLLM, API, conteneur Docker, CI/CD, tests de latence, pertinence, robustesse et traçabilité |

## Livrables

1. Dataset médical bilingue, nettoyé, structuré, anonymisé et documenté.
2. Modèle Qwen3-1.7B adapté par SFT/LoRA puis DPO, avec poids et artefacts reproductibles.
3. Endpoint de démonstration cloud, optimisé par vLLM et accessible par API.
4. Pipeline CI/CD GitHub Actions pour tests et déploiement.
5. Rapport technique de 20 pages maximum : méthode, métriques, analyse, limites et roadmap.

## Critères de succès du POC

- Données traçables, anonymisées et séparées entre entraînement et évaluation.
- Modèle entraîné et évaluable de façon reproductible.
- Réponses structurées, explicables et soumises à des garde-fous.
- Démonstration API fonctionnelle avec mesure de latence et journalisation d’audit.
- Limites et conditions de passage à l’échelle explicitement documentées.

## Sources pédagogiques citées dans la mission

- Cours « Découvrez les enjeux de l’IA générative pour un citoyen européen ».
- Cours « Post-training 101 | Tokens for Thoughts ».
- Cours « Supervised Fine-Tuning — Hugging Face LLM ».
- Hugging Face Datasets, Presidio, PyTorch, Transformers, PEFT/LoRA, MLflow ou Weights & Biases, vLLM, Docker, FastAPI et GitHub Actions.

