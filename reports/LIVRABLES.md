# Livrables du POC CHSA

Date : 2026-09-16 — Statut : `final_candidate`
Sources : CADRAGE_MISSION.md, SPEC_POC_TRIAGE_MEDICAL.md, [consignes officielles de remise](https://openclassrooms.com/fr/paths/2053/projects/3421/8586-livrables-et-soutenance), preuves référencées ci-dessous.

Le [rapport technique](RAPPORT_TECHNIQUE_POC.md) documente la démarche et l’[index des preuves](../docs/evidence/INDEX.md) relie chaque résultat à sa trace. Cette page indique l'état des candidats de remise et leurs limites.

## Parcours de lecture

1. [Rapport technique](RAPPORT_TECHNIQUE_POC.md) : démarche, résultats, infrastructure cloud et limites.
2. [Fiche de soutenance](FICHE_SOUTENANCE.md) : déroulé de démonstration, définitions et réponses aux questions probables.
3. [Index des preuves](../docs/evidence/INDEX.md) : preuves finales citées par le rapport et preuves intermédiaires par étape.
4. Présentation : PowerPoint de 14 slides avec notes orales (généré localement, hors Git) ; plan et notes dans [`PRESENTATION_POC.md`](PRESENTATION_POC.md).

## Livrables demandés par la mission

| Livrable | Fichiers et preuves | État |
|---|---|---|
| Dataset bilingue documenté | [Fiche active](../docs/technical/CORPUS_ETAPE_1_V1.md), [manifeste SFT v2.2](../data/manifests/derived-source-medical-qa-sft-v2.2-privacy-finalized.json), [manifeste DPO v3](../data/manifests/derived-ultramedical-dpo-v3-v22-bound.json), [schéma de métadonnées](../data/manifests/clinical_metadata_v1.schema.json), [processus RGPD](../docs/governance/PROCESSUS_RGPD_CORPUS_V1.md) | 4 700 paires SFT contrôlées ; 480 paires DPO inchangées et réancrées ; publication externe et validation clinique absentes |
| Modèle SFT puis DPO | [SFT v39](../docs/evidence/SFT_V39_RESULT_2026-09-16.md), [recharge v40](../docs/evidence/SFT_V40_RELOAD_RESULT_2026-09-16.md), [DPO v41](../docs/evidence/DPO_V41_RESULT_2026-09-16.md), [sélection v43](../docs/evidence/COMPARISON_V43_RESULT_2026-09-16.md) | SFT et DPO exécutés et vérifiés ; SFT retenu car DPO ne domine pas la revue de développement ; poids lourds privés hors Git |
| Comparaison des modèles | [Test final QA historique v35](../docs/evidence/FINAL_QA_V35_RESULT.md), [revue aveugle v43](../docs/evidence/COMPARISON_V43_RESULT_2026-09-16.md), [réserve finale v46](../docs/evidence/SELECTED_RESERVE_V46_RESULT_2026-09-16.md) | Réserve ouverte une fois sur le SFT retenu : 0/18 JSON conforme, résultat négatif figé et non réutilisé pour régler le système |
| API de démonstration cloud | [Recette Modal](../docs/technical/MODAL_DEPLOYMENT_V1.md), [frontend Cloudflare](../docs/technical/CLOUDFLARE_PAGES_FRONTEND_V1.md), [preuve publique](../docs/evidence/CLOUDFLARE_PAGES_DEPLOYMENT_2026-09-16.md), [garde-fous budgétaires](../docs/evidence/MODAL_BUDGET_GUARDRAILS_2026-09-16.md) | Frontend public HTTPS, Modal T4 scale-to-zero, authentification, deux inférences FR/EN et audit bout en bout observés ; aucune validation clinique |
| CI/CD | [CI](../.github/workflows/ci.yml), [workflow Modal borné](../.github/workflows/deploy-modal.yml), [workflow Cloudflare](../.github/workflows/deploy-cloudflare-pages.yml) | 252 tests, Ruff, build et smoke Docker passés ; workflows de déploiement manuels protégés versionnés ; Direct Upload utilisé pour la preuve Cloudflare actuelle |
| Rapport ≤20 pages | [Source du rapport](RAPPORT_TECHNIQUE_POC.md), [script de génération](../scripts/build_report_pdf.py) | 20 pages A4, généré par `scripts/build_report_pdf.py` ; PDF hors Git ; nom de remise final à confirmer |
| Présentation demandée | [Plan et notes](PRESENTATION_POC.md), [fiche orale](FICHE_SOUTENANCE.md) | PowerPoint 14 slides aligné sur le rapport final, notes orales incluses ; nom de remise final à confirmer |

## Artefacts lourds et confidentialité

Les poids, jeux générés et journaux restent dans les archives privées ; leurs identités sont décrites dans les preuves et manifestes. Le dépôt public ne contient ni token, ni données patient identifiantes, ni poids de modèle. Les fichiers de démonstration sont synthétiques. Les anciennes expériences restent dans `docs/evidence/` et `docs/evidence/archive/` pour la traçabilité et ne décrivent pas l'état courant.

Un résultat de test, un rapport PDF ou une présentation ne remplacent pas une validation clinique. Les priorités et préférences non approuvées restent explicitement proposées.

## Format de remise

ZIP `Titre_du_projet_nom_prenom` ; fichiers `Nom_Prenom_numero_nom_livrable_mmaaaa` (mois de démarrage). Dataset HF/JSONL versionné sur un dépôt, poids finaux chargeables, rapport PDF de 20 pages maximum, URL cloud et CI/CD. Présentation de 15 minutes incluant la démo, puis discussion 10 minutes et débrief 5 minutes. Voir la [fiche de soutenance](FICHE_SOUTENANCE.md) pour la checklist du jour J.
