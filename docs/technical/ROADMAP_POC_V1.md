# Livrables restants du POC de triage médical

- Date : 2026-09-12
- Statut : draft — reprise après audit de la mission
- Sources : [mission](../../CADRAGE_MISSION.md), [audit OpenClassrooms](../evidence/AUDIT_ALIGNEMENT_MISSION_2026-09-12.md), [résultat SFT 500](../evidence/SFT_V22_RESULT_2026-09-12.md).

## État courant

| Livrable | Acquis | À terminer |
|---|---|---|
| Dataset bilingue | Corpus SFT corrigé : 3 721 train, 479 validation, 500 test ; provenance et contrôles documentés. | Finaliser le lot de préférences DPO et expliquer ses limites. |
| Modèle SFT puis DPO | SFT général à 500 étapes sauvegardé, comparaison QA Base/SFT disponible. | Évaluation du parcours de triage, recharge réelle du checkpoint retenu, essai DPO puis comparaison commune. |
| Endpoint cloud vLLM/API | Contrats API, garde-fous, audit et tests avec transport simulé. | Inférence du vrai modèle, mesures de latence et déploiement sur cible autorisée. |
| GitHub Actions | Configuration locale et tests disponibles. | Vérifier l'exécution distante et le déploiement du modèle retenu. |
| Rapport PDF ≤20 pages | Preuves et historique disponibles. | Synthèse finale, résultats comparés, limites et démonstration de soutenance. |

## Ordre de travail

**État courant :** [v23 arrêtée au contrôle de recharge](../evidence/TRIAGE_V23_LAUNCH_2026-09-12.md) : 14/30 générations identiques ; comparaison de triage SFT non exécutée. Ordre d’import corrigé et diagnostic enrichi localement ; [v24 échouée également](../evidence/TRIAGE_V24_LAUNCH_2026-09-12.md). La v25 teste explicitement l’invalidation des copies de poids mises en cache, sans entraînement.

1. Conserver le corpus corrigé et les checkpoints. Aucun nouveau SFT long décidé.
2. Terminer la comparaison Base/SFT avec une partie QA et une partie parcours de triage. Un protocole commun, un budget borné, puis une décision explicite ; les résultats imparfaits sont documentés.
3. Raccorder DPO au SFT retenu, revoir les paires UltraMedical et vérifier un essai court avec référence gelée. Ne pas déduire des préférences biomédicales une validation des niveaux de triage.
4. Comparer Base/SFT/DPO, connecter le vrai modèle à vLLM et à l'API, puis mesurer le parcours complet.
5. Terminer déploiement, CI/CD, rapport et soutenance. Définir la cible et le coût avant toute publication ; le quota Kaggle gratuit reste la seule autorisation GPU actuelle.

## Limites à garder visibles

Les 15 QCM et 30 générations déjà observés ne suffisent pas à conclure à une amélioration générale. Le test final reste isolé. Les scénarios synthétiques et seuils proposés ne sont pas une validation clinique. Le niveau de validation clinique attendu par l'école doit être clarifié avec le mentor, sans confondre cette question et les tâches techniques réalisables.

Le raccord DPO utilise désormais un manifeste du checkpoint et de son tokenizer au lieu d'un hash v5 codé en dur. Cette correction locale ne signifie pas que le DPO a été entraîné ni que le checkpoint 500 a été rechargé sur GPU dans un nouveau processus.

## Historique

Les essais et décisions antérieurs restent dans l'[historique du projet](HISTORIQUE_PROJET_2026-09-11.md), les [preuves](../evidence/) et les [décisions](../decisions/). Cette page remplace l'accumulation de statuts historiques contradictoires ; elle décrit uniquement le travail courant.
