# Livrables restants du POC de triage médical

Date : 2026-09-16 — Statut : draft
Sources : [mission](../../CADRAGE_MISSION.md), [spécification](../../SPEC_POC_TRIAGE_MEDICAL.md), [audit OpenClassrooms](../evidence/AUDIT_ALIGNEMENT_MISSION_2026-09-12.md), preuves liées ci-dessous.

## État courant

| Livrable | Acquis vérifié | À terminer |
|---|---|---|
| Dataset bilingue | Corpus SFT corrigé : 3 721 train, 479 validation, 500 test ; provenance et contrôles documentés. DPO source filtré : 426 train, 54 validation. | Validation clinique des préférences et des références absente ; ne pas l'inventer. |
| SFT puis DPO | SFT 500 et DPO v27 sauvegardés et vérifiés ; comparaison commune QA v28 réalisée. | Comparaison finale QA v35 terminée et vérifiée. Aucun gain de triage DPO démontré. |
| Vrai modèle via API | v34 sur T4 : 18/18 réponses conformes par adaptateur, 8/18 priorités conformes aux références proposées, audit et latence mesurés. | Comparer aussi la Base dans le même runtime API ; traiter les limites de priorité et les contextes incomplets. |
| Collecte complémentaire | API 0.3.0 : suivi explicite des réponses/absences/inconnues, questions FR/EN, raccord testé localement. | Vérifier plusieurs échanges avec le vrai modèle et présenter le parcours complet. |
| Audit | Entrées/sorties anonymisées rapprochées en v34 ; ajout et relecture après deux processus API locaux vérifiés ; synchronisation avant restitution. | Persistance sur la cible distante et politique de conservation de cette cible. |
| Déploiement et GitHub Actions | Recette Docker et workflow de tests écrits ; configuration locale contrôlée. | Cible autorisée, accès extérieur privé, déploiement automatisé et preuve distante. |
| Rapport et soutenance | Rapport Markdown actualisé, historique et preuves disponibles. | Résultats finaux, PDF ≤20 pages vérifié et démonstration. Le PDF historique reste un brouillon périmé. |

## Ordre de travail

1. La [comparaison QA v35](../evidence/FINAL_QA_V35_RESULT.md) est terminée : fichiers et calculs vérifiés sur les 500 exemples réservés et 50 générations déterministes par modèle. Le protocole est figé ; les résultats ne serviront pas à régler les modèles.
2. Terminer la démonstration réelle de collecte et la comparaison API Base/SFT/DPO. Le [candidat avec dialogues](VLLM_DEMONSTRATION_V1.md) a été lancé comme v36 le 16 septembre ; il inclut la synchronisation d'audit et les trois variantes. Aucun nouveau SFT ni DPO n'est décidé.
3. Évaluer les contrôles du parcours et la pertinence des réponses sur les scénarios de développement. La collecte structurée ne résout pas à elle seule les erreurs de priorité ou les faits inventés. Les seuils et références restent proposés, sans approbation clinique.
4. Finaliser une cible cloud et son accès autorisés, le stockage/rétention, puis GitHub Actions avec déploiement et smoke test. Le notebook privé Kaggle sur quota gratuit est la seule autorisation GPU actuelle. Son API en boucle locale ne constitue pas un endpoint accessible depuis l'extérieur.
5. Produire le PDF final et dérouler la soutenance sur les preuves obtenues, avec les résultats négatifs et les limites explicites.

## Preuves et limites

La [v34](../evidence/VLLM_API_V34_RESULT.md) a résolu les sorties incomplètes de ce lot, mais les deux adaptateurs n'utilisent jamais `moderate` et omettent les questions sur les cas insuffisants. Les six scénarios critiques proposés sont classés `maximum`, sans que cela établisse une sûreté clinique générale.

La régression locale complète passe 171 tests à la révision a66a3e2, le 16 septembre. La [collecte locale](../evidence/COLLECTE_COMPLEMENTAIRE_LOCALE_2026-09-14.md) avait auparavant été vérifiée à la révision 1756f1b. L'ajout ultérieur de synchronisation et la [preuve de redémarrage](../evidence/AUDIT_RESTART_LOCAL_2026-09-14.md) passent 14 tests ciblés. Ces tests ne sont pas des résultats GPU avec le nouveau prompt.

La v35 utilise Transformers FP4 et des questions-réponses libres ; l'API utilise vLLM FP16 et des sorties contraintes. Leurs métriques ne sont pas interchangeables. Une baisse de loss ne prouve pas une meilleure priorité de triage.

## Historique

Les essais précédents restent dans l'[historique du projet](HISTORIQUE_PROJET_2026-09-11.md), les [preuves](../evidence/) et les [décisions](../decisions/). Cette page décrit l'état courant ; elle ne remplace aucune preuve ni exigence du mandat.
