# Livrables du POC CHSA

Date : 2026-09-16 — Statut : draft, livraison en cours
Sources : CADRAGE_MISSION.md, SPEC_POC_TRIAGE_MEDICAL.md, [consignes officielles de remise](https://openclassrooms.com/fr/paths/2053/projects/3421/8586-livrables-et-soutenance), preuves référencées ci-dessous.

Le [guide de reprise](../GUIDE_REPRISE.md) pilote désormais la réalisation. Cette liste décrit les artefacts existants, sans les déclarer finaux.

## Parcours de lecture

1. [Rapport technique](RAPPORT_TECHNIQUE_POC.md) : démarche, résultats et limites. Candidat PDF de cinq pages généré et contrôlé après la réserve v46.
2. [Déroulé de démonstration](DEMONSTRATION_POC.md) : présentation du parcours et preuves à montrer.
3. [Guide de reprise](../GUIDE_REPRISE.md) : acquis vérifiés, séquence réalisée et écarts externes restants.
4. PowerPoint local de dix slides — candidat v46 généré, contrôlé et cohérent avec le rapport.

## Livrables demandés par la mission

| Livrable | Fichiers et preuves | État |
|---|---|---|
| Dataset bilingue documenté | [Fiche active](../docs/technical/CORPUS_ETAPE_1_V1.md), [manifeste SFT v2.2](../data/manifests/derived-source-medical-qa-sft-v2.2-privacy-finalized.json), [manifeste DPO v3](../data/manifests/derived-ultramedical-dpo-v3-v22-bound.json), [schéma de métadonnées](../data/manifests/clinical_metadata_v1.schema.json), [processus RGPD](../docs/governance/PROCESSUS_RGPD_CORPUS_V1.md) | 4 700 paires SFT contrôlées ; 480 paires DPO inchangées et réancrées ; publication externe et validation clinique absentes |
| Modèle SFT puis DPO | [SFT v39](../docs/evidence/SFT_V39_RESULT_2026-09-16.md), [recharge v40](../docs/evidence/SFT_V40_RELOAD_RESULT_2026-09-16.md), [DPO v41](../docs/evidence/DPO_V41_RESULT_2026-09-16.md), [sélection v43](../docs/evidence/COMPARISON_V43_RESULT_2026-09-16.md) | SFT et DPO exécutés et vérifiés ; SFT retenu car DPO ne domine pas la revue de développement ; poids lourds privés hors Git |
| Comparaison des modèles | [Test final QA historique v35](../docs/evidence/FINAL_QA_V35_RESULT.md), [revue aveugle v43](../docs/evidence/COMPARISON_V43_RESULT_2026-09-16.md), [réserve finale v46](../docs/evidence/SELECTED_RESERVE_V46_RESULT_2026-09-16.md) | Réserve ouverte une fois sur le SFT retenu : 0/18 JSON conforme, résultat négatif figé et non réutilisé pour régler le système |
| API de démonstration cloud | [Recette vLLM](../docs/technical/VLLM_DEMONSTRATION_V1.md), [parcours Kaggle + Cloudflare à 0 €](../docs/technical/DEMONSTRATION_KAGGLE_CLOUDFLARE_V1.md), [collecte](../docs/technical/COLLECTE_COMPLEMENTAIRE_V1.md) | Inférence locale sur GPU Kaggle prouvée ; notebook d'exposition éphémère préparé et testé localement ; URL et smoke extérieurs à observer |
| CI/CD | [CI](../.github/workflows/ci.yml), [préparation sans dépense](../docs/evidence/FREE_DEMO_PREPARATION_2026-09-16.md), [ancienne CD Modal archivée](../.github/workflows/deploy-modal.yml) | CI distante tests/conteneur passée ; workflow payant désactivé ; Quick Tunnel interactif, donc aucune CD GPU permanente prouvée |
| Rapport ≤20 pages | [Source du rapport](RAPPORT_TECHNIQUE_POC.md), [preuve du candidat PDF v46](../docs/evidence/REPORT_PDF_V46_MODAL_READY_2026-09-16.md) | Candidat A4 de cinq pages vérifié après préparation Modal ; nom de remise final à confirmer |
| PowerPoint demandé | [Preuve du support v46](../docs/evidence/PRESENTATION_V46_2026-09-16.md) | Dix slides vérifiées, quatre graphiques natifs ; nom de remise final à confirmer |

## Artefacts lourds et confidentialité

Les poids, jeux générés et journaux restent dans les archives privées ; leurs identités sont décrites dans les preuves et manifestes. Le dépôt public ne contient ni token, ni données patient identifiantes, ni poids de modèle. Les fichiers de démonstration sont synthétiques. Les anciennes expériences restent dans `docs/evidence/` pour la traçabilité et ne décrivent pas l'état courant.

Un résultat de test, un rapport PDF ou une présentation ne remplacent pas une validation clinique. Les priorités et préférences non approuvées restent explicitement proposées.

## Format de remise

ZIP `Titre_du_projet_nom_prenom` ; fichiers `Nom_Prenom_numero_nom_livrable_mmaaaa` (mois de démarrage). Dataset HF/JSONL versionné sur un dépôt, poids finaux chargeables, rapport PDF de 20 pages maximum, URL cloud et CI/CD. Présentation de 15 minutes incluant la démo, puis discussion 10 minutes et débrief 5 minutes. Voir le guide pour la checklist complète.
