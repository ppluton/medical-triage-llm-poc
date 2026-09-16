# Livrables restants du POC de triage médical

Date : 2026-09-16 — Statut : superseded pour le pilotage
Sources : [mission](../../CADRAGE_MISSION.md), [spécification](../../SPEC_POC_TRIAGE_MEDICAL.md), [audit OpenClassrooms](../evidence/AUDIT_ALIGNEMENT_MISSION_2026-09-12.md), preuves liées ci-dessous.

> Le [guide de reprise](../../GUIDE_REPRISE.md) remplace cet ordre de travail à la demande de Pierre. Cette page conserve l’état de la première réalisation.

## État de la première réalisation

| Livrable | Acquis vérifié | À terminer |
|---|---|---|
| Dataset bilingue | Corpus SFT corrigé : 3 721 train, 479 validation, 500 test ; provenance et contrôles documentés. DPO source filtré : 426 train, 54 validation. | Validation clinique des préférences et des références absente ; ne pas l'inventer. |
| SFT puis DPO | SFT 500 et DPO v27 sauvegardés et vérifiés ; comparaison commune QA v28 réalisée. | Comparaison finale QA v35 terminée et vérifiée. Aucun gain de triage DPO démontré. |
| Vrai modèle via API | v36 compare Base/SFT/DPO ; API 0.4.0 et garde-fous v1 vérifiés localement puis rejoués sur les sorties historiques. | Exécuter le candidat v37 avec le vrai runtime et mesurer corrections/fallbacks ; le replay n'est pas une inférence. |
| Collecte complémentaire | Suivi explicite des réponses/absences/inconnues, questions FR/EN, raccord et garde-fous API 0.4.0 testés localement. | Vérifier plusieurs échanges avec le vrai modèle et présenter le parcours complet. |
| Audit | Entrées/sorties anonymisées rapprochées en v34 ; ajout et relecture après deux processus API locaux vérifiés ; synchronisation avant restitution. | Persistance sur la cible distante et politique de conservation de cette cible. |
| Déploiement et GitHub Actions | Recette Docker, CI distante et démonstration Kaggle + Cloudflare à 0 € préparée localement. | Exécution extérieure, smoke distant et preuve ; une CD GPU permanente reste hors free tier. |
| Rapport et soutenance | Rapport Markdown actualisé, historique et preuves disponibles. | Résultats finaux, PDF ≤20 pages vérifié et démonstration. Le PDF historique reste un brouillon périmé. |

## Ordre de travail

1. La [comparaison QA v35](../evidence/FINAL_QA_V35_RESULT.md) est terminée : fichiers et calculs vérifiés sur les 500 exemples réservés et 50 générations déterministes par modèle. Le protocole est figé ; les résultats ne serviront pas à régler les modèles.
2. Terminer la démonstration réelle de collecte et la comparaison API Base/SFT/DPO. Le [candidat avec dialogues](VLLM_DEMONSTRATION_V1.md) a été lancé comme v36 le 16 septembre ; l'API 0.4.0 et ses garde-fous ont ensuite été testés localement et rejoués hors ligne. Le candidat v37 avec vraie inférence reste à exécuter. Aucun nouveau SFT ni DPO n'est décidé.
3. Mesurer les corrections et remplacements conservateurs sur le runtime réel. Le replay v36 améliore les mesures critiques proposées mais remplace la majorité des sorties SFT/DPO ; cela contient les défauts connus sans démontrer une meilleure qualité du modèle. Les seuils et références restent proposés, sans approbation clinique.
4. Exécuter la [démonstration Kaggle + Cloudflare](DEMONSTRATION_KAGGLE_CLOUDFLARE_V1.md) à dépense nulle, puis conserver le smoke et l'audit. Le code local ne prouve pas encore l'URL extérieure et Quick Tunnel n'est pas une CD GPU permanente.
5. Produire le PDF final et dérouler la soutenance sur les preuves obtenues, avec les résultats négatifs et les limites explicites.

## Preuves et limites

La [v34](../evidence/VLLM_API_V34_RESULT.md) a résolu les sorties incomplètes de ce lot, mais les deux adaptateurs n'utilisent jamais `moderate` et omettent les questions sur les cas insuffisants. Les six scénarios critiques proposés sont classés `maximum`, sans que cela établisse une sûreté clinique générale.

La régression locale complète passe 171 tests à la révision a66a3e2, le 16 septembre. La [collecte locale](../evidence/COLLECTE_COMPLEMENTAIRE_LOCALE_2026-09-14.md) avait auparavant été vérifiée à la révision 1756f1b. L'ajout ultérieur de synchronisation et la [preuve de redémarrage](../evidence/AUDIT_RESTART_LOCAL_2026-09-14.md) passent 14 tests ciblés. Ces tests ne sont pas des résultats GPU avec le nouveau prompt.

La v35 utilise Transformers FP4 et des questions-réponses libres ; l'API utilise vLLM FP16 et des sorties contraintes. Leurs métriques ne sont pas interchangeables. Une baisse de loss ne prouve pas une meilleure priorité de triage.

## Historique

Les essais précédents restent dans l'[historique du projet](HISTORIQUE_PROJET_2026-09-11.md), les [preuves](../evidence/) et les [décisions](../decisions/). Cette page décrit l'état courant ; elle ne remplace aucune preuve ni exigence du mandat.
