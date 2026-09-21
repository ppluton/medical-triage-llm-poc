# Documentation du projet

Date : 2026-09-21 — Statut : current
Sources : mission OpenClassrooms, cadrage et spécification du dépôt.

## Parcours de lecture

1. [Rapport technique](../reports/RAPPORT_TECHNIQUE_POC.md) — démarche, résultats, infrastructure et limites ; point d’entrée principal.
2. [Index des preuves](evidence/INDEX.md) — preuves finales citées par le rapport, puis preuves intermédiaires par étape.
3. [Notes d’apprentissage](learning/README.md) — explications pédagogiques numérotées, sans valeur de preuve.
4. [Livrables](../reports/LIVRABLES.md) et [fiche de soutenance](../reports/FICHE_SOUTENANCE.md) — état de la remise et déroulé de démonstration.
5. [Configurations](../configs/README.md) — configurations actives de la chaîne finale et versions historiques.

## Documents techniques de référence

- [Corpus de l’étape 1](technical/CORPUS_ETAPE_1_V1.md) — sources, SFT, DPO, métadonnées et portes restantes.
- [Processus RGPD du corpus](governance/PROCESSUS_RGPD_CORPUS_V1.md) — méthode, preuves et limites.
- [Déploiement Modal v1](technical/MODAL_DEPLOYMENT_V1.md) — endpoint GPU T4 déployé, protégé et configuré en scale-to-zero.
- [Frontend Cloudflare Pages](technical/CLOUDFLARE_PAGES_FRONTEND_V1.md) — frontend public sur `triage-poc.pierrepluton.com`, proxy sécurisé raccordé à Modal.
- [Démonstration Kaggle + Cloudflare](technical/DEMONSTRATION_KAGGLE_CLOUDFLARE_V1.md) — secours éphémère sans dépense, dont le premier run dédié a échoué avant vLLM.

## Archives

- [Spécification d’exécution](archive/SPEC_EXECUTION_V1.md) et [guide de reprise](archive/GUIDE_REPRISE.md) — plans de travail `superseded`, conservés pour l’historique.
- [Preuves archivées](evidence/archive/) — preuves intermédiaires non citées par les points d’entrée.
- [Historique documentaire](HISTORIQUE_DOCUMENTAIRE.md) — anciennes étapes et liens conservés.

Le [cadrage](../CADRAGE_MISSION.md) et la [spécification](../SPEC_POC_TRIAGE_MEDICAL.md) restent les références ; ce dossier ne réduit pas leurs exigences.

| Dossier | Usage |
|---|---|
| `technical/` | Contrats, recettes et preuves de reproductibilité ; vérifier date et périmètre avant emploi |
| `evidence/` | Résultats datés, y compris les échecs ; jamais une autorisation implicite de relancer |
| `governance/` | Sources, licences, anonymisation et risques |
| `decisions/` | Choix et hypothèses, avec leur statut |
| `learning/` | Explications pédagogiques et retour d’expérience |

Les données, poids et sorties volumineuses restent hors Git. Les brouillons de rapport et de présentation ne prouvent pas la livraison. Les preuves non citées sont déplacées dans `evidence/archive/` plutôt que supprimées.
