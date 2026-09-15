# Livrables du POC CHSA

Date : 2026-09-16 — Statut : draft, livraison en cours
Sources : CADRAGE_MISSION.md, SPEC_POC_TRIAGE_MEDICAL.md, preuves référencées ci-dessous.

## Parcours de lecture

1. [Rapport technique](RAPPORT_TECHNIQUE_POC.md) : démarche, résultats et limites. Export PDF final de 20 pages maximum à produire après consolidation des dernières mesures.
2. [Déroulé de démonstration](DEMONSTRATION_POC.md) : présentation du parcours et preuves à montrer.
3. [Feuille de route](../docs/technical/ROADMAP_POC_V1.md) : acquis et écarts restants.
4. PowerPoint pédagogique : à produire par l'agent Sol après vérification des dernières mesures, puis à relire et contrôler visuellement.

## Livrables demandés par la mission

| Livrable | Fichiers et preuves | État |
|---|---|---|
| Dataset bilingue documenté | [Manifeste SFT corrigé](../data/manifests/derived-source-medical-qa-sft-v2.1-reviewed.json), [gouvernance](../docs/governance/), [scripts reproductibles](../scripts/) | Corpus construit ; données brutes conservées hors Git ; validation clinique absente |
| Modèle SFT puis DPO | [Identité SFT](../configs/sft-v22-handoff.json), [SFT v22](../docs/evidence/SFT_V22_RESULT_2026-09-12.md), [DPO v27](../docs/evidence/DPO_V27_RESULT_2026-09-13.md) | Poids archivés et empreintes vérifiées ; poids volumineux hors Git |
| Comparaison des modèles | [Test final QA v35](../docs/evidence/FINAL_QA_V35_RESULT.md), [API v34](../docs/evidence/VLLM_API_V34_RESULT.md) | QA terminée ; comparaison API enrichie v36 en cours |
| API de démonstration cloud | [Recette vLLM](../docs/technical/VLLM_DEMONSTRATION_V1.md), [Docker Compose](../compose.demo.yaml), [collecte](../docs/technical/COLLECTE_COMPLEMENTAIRE_V1.md) | Inférence locale sur GPU Kaggle prouvée ; accès extérieur autorisé restant à établir |
| CI/CD | [Workflow GitHub Actions](../.github/workflows/ci.yml) | Tests et conteneur configurés ; déploiement automatique et preuve distante à achever |
| Rapport ≤20 pages | [Source du rapport](RAPPORT_TECHNIQUE_POC.md) | Source mise à jour ; PDF final à produire |
| PowerPoint demandé | Démarche, résultats, démonstration et limites avec notes orales | À produire à la fin et à vérifier |

## Artefacts lourds et confidentialité

Les poids, jeux générés et journaux restent dans les archives privées ; leurs identités sont décrites dans les preuves et manifestes. Le dépôt public ne contient ni token, ni données patient identifiantes, ni poids de modèle. Les fichiers de démonstration sont synthétiques. Les anciennes expériences restent dans `docs/evidence/` pour la traçabilité et ne décrivent pas l'état courant.

Un résultat de test, un rapport PDF ou une présentation ne remplacent pas une validation clinique. Les priorités et préférences non approuvées restent explicitement proposées.
