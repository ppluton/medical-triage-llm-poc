# Documentation du projet

Date : 2026-09-16 — Statut : draft
Sources : mission OpenClassrooms, cadrage et spécification du dépôt.

## Commencer ici

1. [Spécification d’exécution](../SPEC_EXECUTION_V1.md) — stack et livrables.
2. [Guide de reprise étape par étape](../GUIDE_REPRISE.md) — plan actif, preuves attendues et prochaine action.
3. [Bilan des erreurs et corrections](learning/RETOUR_EXPERIENCE_REPRISE_2026-09-16.md) — ce que nous conservons et ce que nous changeons.
4. [Corpus de l’étape 1](technical/CORPUS_ETAPE_1_V1.md) — sources, SFT, DPO, métadonnées et portes restantes.
5. [Processus RGPD du corpus](governance/PROCESSUS_RGPD_CORPUS_V1.md) — méthode, preuves et limites.
6. [Livrables](../reports/LIVRABLES.md) — fichiers attendus pour la remise.
7. [Déploiement Modal v1](technical/MODAL_DEPLOYMENT_V1.md) — cible pilote principale, bornée à 5 USD de crédits et 0 USD de dépense nette, non encore déployée.
8. [Frontend Cloudflare Pages](technical/CLOUDFLARE_PAGES_FRONTEND_V1.md) — frontend public sur `triage-poc.pierrepluton.com`, proxy sécurisé en attente de Modal.
9. [Démonstration Kaggle + Cloudflare](technical/DEMONSTRATION_KAGGLE_CLOUDFLARE_V1.md) — secours éphémère sans dépense, dont le premier run dédié a échoué avant vLLM.
10. [Historique documentaire](HISTORIQUE_DOCUMENTAIRE.md) — anciennes étapes et liens conservés.

Le [cadrage](../CADRAGE_MISSION.md) et la [spécification](../SPEC_POC_TRIAGE_MEDICAL.md) restent les références. Le guide organise leur réalisation ; il ne réduit pas leurs exigences.

| Dossier | Usage |
|---|---|
| `technical/` | Contrats, recettes et preuves de reproductibilité ; vérifier date et périmètre avant emploi |
| `evidence/` | Résultats datés, y compris les échecs ; jamais une autorisation implicite de relancer |
| `governance/` | Sources, licences, anonymisation et risques |
| `decisions/` | Choix et hypothèses, avec leur statut |
| `learning/` | Explications pédagogiques et retour d’expérience |

Les données, poids et sorties volumineuses restent hors Git. Les brouillons de rapport et de présentation ne prouvent pas la livraison. Une note historique reste à son adresse pour préserver les références des expériences.
