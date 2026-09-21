# Spécification d’exécution — première livraison CHSA

Date : 2026-09-16 — Statut : `superseded` (archivé le 2026-09-21 ; plan d’implémentation de la première livraison, remplacé par le [rapport technique](../../reports/RAPPORT_TECHNIQUE_POC.md))
Responsable : Pierre. Échéance : **17 septembre 2026, 15 h Paris / 17 h Tbilissi**.
Budget : **Kaggle privé gratuit uniquement**. Aucun GPU payant.

Sources : [mission officielle](https://openclassrooms.com/fr/paths/2053/projects/3421/8585-mission---developpez-le-poc-d'un-agent-de-triage-medical), [livrables et soutenance](https://openclassrooms.com/fr/paths/2053/projects/3421/8586-livrables-et-soutenance), [cadrage](../../CADRAGE_MISSION.md), [spécification de référence](../../SPEC_POC_TRIAGE_MEDICAL.md). Les deux pages ont été relues intégralement, y compris les étapes détaillées. Ce document rend les attentes exécutables ; il ne remplace pas les références.

## 1. Produit à démontrer

Un assistant bilingue FR/EN de triage initial, sur scénarios synthétiques. Il recueille les symptômes, pose des questions adaptées aux informations manquantes, propose `maximum`, `moderate` ou `deferred`, explique sa réponse, rappelle le recours au professionnel et crée une trace d’audit. Une API documentée démontre l’intégrabilité ; aucune connexion à un vrai SI hospitalier n’est revendiquée.

## 2. Stack retenue

| Élément | Choix pour cette livraison | Rôle |
|---|---|---|
| Données | Hugging Face Datasets, export JSONL | Charger, transformer et versionner les corpus |
| Anonymisation | Presidio AnalyzerEngine + AnonymizerEngine, spaCy FR/EN | Détection, masquage et revue de la conservation du sens |
| Modèle | **Qwen3-1.7B-Base**, révision épinglée | Même base pour toutes les comparaisons |
| SFT | PyTorch, Transformers, PEFT/LoRA ; recette Unsloth compatible sur Kaggle | Spécialisation supervisée, petit essai puis entraînement |
| DPO | TRL DPOTrainer avec PEFT, depuis le SFT retenu | Préférences chosen/rejected ; pas de remplacement par GRPO |
| Tracking | **MLflow local**, fichiers exportés hors Git | Paramètres, seed, métriques et chemins/checksums des checkpoints |
| Calcul | Notebook Kaggle privé existant `pierrepluton/chsa-source-sft-qwen3` | GPU gratuit ; versions et données figées |
| Inférence | **vLLM** | Servir les adaptateurs retenus et mesurer la latence |
| API | **FastAPI**, schémas Pydantic | Collecte, validation, appel modèle et audit |
| Packaging | **Docker** | Environnement reproductible |
| CI/CD | **GitHub Actions** | Tests, build, déploiement pilote et smoke test distant |

Qwen, SFT/LoRA, DPO, vLLM, Docker, FastAPI et GitHub Actions viennent de la mission. Les outils de données/anonymisation et de tracking sont cités dans ses étapes ; cette spécification fixe HF/Presidio/MLflow pour éviter de multiplier les alternatives. MLflow est à implémenter : les anciens logs natifs ne prouvent pas son utilisation. Unsloth est une recette d’accélération, pas un fournisseur cloud ni une garantie de vitesse ; les anciens défauts de terminaison/précision doivent rester couverts dans le runtime retenu.

Aucun ajout de modèle plus gros, RAG, agent framework ou interface complexe pour cette première version.

## 3. Corpus à livrer

Sources : MediQAl, FrenchMedMCQA, MedQuAD pour SFT ; UltraMedical-Preference pour DPO. Environ 5 000 exemples SFT bilingues, avec exclusions justifiées. Ne pas inventer des labels de triage absents des sources.

- SFT : identifiant, langue, instruction complète, réponse complète, source/version/licence, transformations, statut d’anonymisation, statut de revue et split.
- DPO : identifiant, prompt commun, chosen, rejected, provenance et justification de préférence disponible, langue, statut de revue et split.
- Métadonnées cliniques : symptômes, antécédents, constantes et confiance lorsqu’ils sont disponibles ; absence explicite sinon, sans extraction présentée comme validation.
- Séparer train/validation/test par groupes ; réserver une évaluation clinique distincte. Le test v35 déjà lu n’est pas un nouveau test aveugle.
- Préserver tous les choix QCM et les réponses. Rejeter/documenter les dépassements plutôt que tronquer silencieusement.
- Contrôler le masquage et relire des exemples source → canonique → texte tokenisé en FR et EN pour chaque source.

**Livraison :** JSONL ou Hugging Face Dataset, data card, comptages, schéma, hashes, journal des transformations et version du dépôt. Données/poids conservés hors Git public ; mode de mise à disposition autorisé et licences vérifiés. Une préférence source n’est pas une validation clinique du projet.

## 4. Entraînement et comparaison

1. Figer le corpus, la révision Qwen, le template, les paramètres et les jeux d’évaluation.
2. Mesurer la Base ; vérifier les labels, le masquage du prompt et le signal de fin.
3. Faire un essai LoRA court avec sauvegarde/recharge. Mesurer débit et mémoire pour estimer la durée ; expliquer le passage au SFT complet à Pierre.
4. Exécuter le SFT, enregistrer logs/checkpoints et choisir sur validation.
5. Exécuter le DPO depuis ce checkpoint avec référence vérifiée ; vérifier changement des poids et recharge.
6. Comparer Base/SFT/DPO sur les mêmes entrées et réglages dans chaque protocole. Ne pas comparer directement QA Transformers quantifiée et API vLLM FP16 comme s’il s’agissait de la même mesure.

**Mesures :** loss et exactitude QA lorsque mesurable ; arrêts/répétitions ; distribution et matrice des priorités, sous/sur-triage, rappel des cas critiques, faits inventés et réponses dangereuses, questions/explications ; différences FR/EN. Références et seuils cliniques : `proposed` jusqu’à validation explicite. La revue humaine et les scores automatiques sont séparés.

**Décision :** un format valide ou une loss qui baisse ne suffit pas. Documenter les régressions et l’absence de gain DPO ; ne pas multiplier les runs sans cause identifiée. Un nouvel entraînement est suivi d’une évaluation avant utilisation dans la démo.

## 5. Contrat API et démonstration

`POST /v1/triage` reçoit `language` et `patient_context` : âge/groupe, symptômes, durée, évolution, intensité, signes associés, antécédents, allergies, traitements, constantes et vulnérabilités. Distinguer absent, inconnu et indisponible.

Réponse : identifiant, priorité parmi les trois valeurs, synthèse, explication, informations manquantes/questions, avertissement, version du modèle et latence. Questions adaptées aux réponses déjà obtenues ; ne pas répéter une information explicitement indisponible. Contrôles de schéma et confidentialité ; échec explicite si fournisseur indisponible.

Audit : identifiant, date, versions modèle/prompt/contrôles, entrée anonymisée, sortie, statut et latence. Accès restreint et aucun secret dans les logs. Vérifier persistance et rapprochement des interactions.

Démo FR/EN : douleur thoracique, détresse respiratoire, neurologie, pédiatrie, grossesse, vulnérabilité, informations insuffisantes et contradictoires. Montrer au moins un parcours multi-échanges. Mesurer p50/p95, débit, erreurs, robustesse et audit ; distinguer résultat proposé et validation clinique.

## 6. Déploiement et CI/CD

FastAPI et vLLM conteneurisés. GitHub Actions exécute lint/tests, schémas/anonymisation, build Docker, intégration API, déploiement sur cible autorisée, puis smoke test depuis l’extérieur. Fournir un mode d’accès pour le jury, une procédure de relance/arrêt et les limites d’usage.

**Écart à résoudre tôt :** Kaggle gratuit est autorisé pour le calcul ; son service localhost n’est pas un endpoint cloud accessible au jury. La cible gratuite accessible et son autorisation restent à établir. Ne pas remplacer ce livrable par une capture d’écran ou annoncer un déploiement qui n’a pas eu lieu.

## 7. Dossier de remise et validation finale

| À remettre | Vérification avant ZIP |
|---|---|
| Dataset HF/JSONL versionné | Chargement, splits, schéma, traçabilité et data card |
| Modèle SFT/LoRA puis DPO | Base exacte, poids/adaptateurs, tokenizer, hashes, procédure de recharge exécutée |
| Endpoint cloud vLLM | Accès réel depuis l’extérieur, scénario FR/EN et audit |
| CI/CD GitHub Actions | Workflow et exécution incluant déploiement/smoke test |
| Rapport PDF ≤20 pages | Ouverture, pagination, chiffres sourcés, limites et roadmap |
| PowerPoint pédagogique | Ouverture, lisibilité, démo et notes ; durée 15 min ±5 |

ZIP `Titre_du_projet_nom_prenom` ; fichiers `Nom_Prenom_numero_nom_livrable_mmaaaa`, mois de démarrage à confirmer. Discussion 10 min après présentation, puis débrief 5 min.

Un dossier de première version distingue les éléments livrés et manquants. La livraison complète exige toutes les preuves ci-dessus. Le [guide](GUIDE_REPRISE.md) donne l’ordre de travail ; le [retour d’expérience](../learning/63-retour-experience-reprise.md) conserve les erreurs à ne pas reproduire.
