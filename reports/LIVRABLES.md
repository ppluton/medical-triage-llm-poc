# Livrables du POC CHSA

Date : 2026-09-16 — Statut : draft, livraison en cours
Sources : CADRAGE_MISSION.md, SPEC_POC_TRIAGE_MEDICAL.md, [consignes officielles de remise](https://openclassrooms.com/fr/paths/2053/projects/3421/8586-livrables-et-soutenance), preuves référencées ci-dessous.

Le [guide de reprise](../GUIDE_REPRISE.md) pilote désormais la réalisation. Cette liste décrit les artefacts existants, sans les déclarer finaux.

## Parcours de lecture

1. [Rapport technique](RAPPORT_TECHNIQUE_POC.md) : démarche, résultats et limites. Export PDF final de 20 pages maximum à produire après consolidation des dernières mesures.
2. [Déroulé de démonstration](DEMONSTRATION_POC.md) : présentation du parcours et preuves à montrer.
3. [Feuille de route](../docs/technical/ROADMAP_POC_V1.md) : acquis et écarts restants.
4. PowerPoint et storyboard locaux — brouillon de première réalisation préparé par Sol ; finalisation suspendue pendant la reprise.

## Livrables demandés par la mission

| Livrable | Fichiers et preuves | État |
|---|---|---|
| Dataset bilingue documenté | [Fiche active](../docs/technical/CORPUS_ETAPE_1_V1.md), [manifeste SFT corrigé](../data/manifests/derived-source-medical-qa-sft-v2.1-reviewed.json), [schéma de métadonnées](../data/manifests/clinical_metadata_v1.schema.json), [processus RGPD](../docs/governance/PROCESSUS_RGPD_CORPUS_V1.md) | 4 700 paires SFT contrôlées et lot DPO revu pour le POC ; lignée DPO et revue contextuelle PII à consolider |
| Modèle SFT puis DPO | [Identité SFT](../configs/sft-v22-handoff.json), [SFT v22](../docs/evidence/SFT_V22_RESULT_2026-09-12.md), [DPO v27](../docs/evidence/DPO_V27_RESULT_2026-09-13.md) | Poids archivés et empreintes vérifiées ; poids volumineux hors Git |
| Comparaison des modèles | [Test final QA v35](../docs/evidence/FINAL_QA_V35_RESULT.md), [API v34](../docs/evidence/VLLM_API_V34_RESULT.md) | QA terminée ; comparaison API enrichie v36 en cours |
| API de démonstration cloud | [Recette vLLM](../docs/technical/VLLM_DEMONSTRATION_V1.md), [Docker Compose](../compose.demo.yaml), [collecte](../docs/technical/COLLECTE_COMPLEMENTAIRE_V1.md) | Inférence locale sur GPU Kaggle prouvée ; accès extérieur autorisé restant à établir |
| CI/CD | [Workflow GitHub Actions](../.github/workflows/ci.yml) | Tests et conteneur configurés ; déploiement automatique et preuve distante à achever |
| Rapport ≤20 pages | [Source du rapport](RAPPORT_TECHNIQUE_POC.md) | Source mise à jour ; PDF final à produire |
| PowerPoint demandé | Démarche, résultats, démonstration et limites avec notes orales | À produire à la fin et à vérifier |

## Artefacts lourds et confidentialité

Les poids, jeux générés et journaux restent dans les archives privées ; leurs identités sont décrites dans les preuves et manifestes. Le dépôt public ne contient ni token, ni données patient identifiantes, ni poids de modèle. Les fichiers de démonstration sont synthétiques. Les anciennes expériences restent dans `docs/evidence/` pour la traçabilité et ne décrivent pas l'état courant.

Un résultat de test, un rapport PDF ou une présentation ne remplacent pas une validation clinique. Les priorités et préférences non approuvées restent explicitement proposées.

## Format de remise

ZIP `Titre_du_projet_nom_prenom` ; fichiers `Nom_Prenom_numero_nom_livrable_mmaaaa` (mois de démarrage). Dataset HF/JSONL versionné sur un dépôt, poids finaux chargeables, rapport PDF de 20 pages maximum, URL cloud et CI/CD. Présentation de 15 minutes incluant la démo, puis discussion 10 minutes et débrief 5 minutes. Voir le guide pour la checklist complète.
