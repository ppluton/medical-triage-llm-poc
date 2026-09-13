# Livrables restants du POC de triage médical

- Date : 2026-09-13
- Statut : draft — reprise après audit de la mission
- Sources : [mission](../../CADRAGE_MISSION.md), [audit OpenClassrooms](../evidence/AUDIT_ALIGNEMENT_MISSION_2026-09-12.md), [résultat SFT 500](../evidence/SFT_V22_RESULT_2026-09-12.md).

## État courant

| Livrable | Acquis | À terminer |
|---|---|---|
| Dataset bilingue | Corpus SFT corrigé : 3 721 train, 479 validation, 500 test ; provenance et contrôles documentés. | Lot DPO 426/54 admis pour expérimentation ; validation clinique absente. |
| Modèle SFT puis DPO | SFT général à 500 étapes sauvegardé, comparaison QA Base/SFT disponible. | DPO v27 exécuté, sauvegarde vérifiée ; comparaison commune v28 terminée, sans gain de triage DPO. |
| Endpoint cloud vLLM/API | Contrats API, garde-fous, audit et tests avec transport simulé. | Inférence du vrai modèle, mesures de latence et déploiement sur cible autorisée. |
| GitHub Actions | Configuration locale et tests disponibles. | Vérifier l'exécution distante et le déploiement du modèle retenu. |
| Rapport PDF ≤20 pages | Preuves et historique disponibles. | Synthèse finale, résultats comparés, limites et démonstration de soutenance. |

## Ordre de travail

**État courant :** [v26 terminée](../evidence/TRIAGE_V26_RESULT_2026-09-12.md) : recharge 30/30 identique, consigne explicite. SFT : 12/18 JSON conformes, 6/18 priorités conformes, 2/6 cas critiques avec sortie valide et maximum correct. Qualité insuffisante, dont faits inventés. Le [DPO miniature CPU](../evidence/DPO_CPU_MECHANICS_2026-09-12.md) vérifie la mécanique des deux adaptateurs ; le lot 426/54 a été admis pour expérimentation pédagogique selon ADR-014 et la [v27 DPO](../evidence/DPO_V27_LAUNCH_2026-09-12.md) est terminée : 20 étapes, 392 tenseurs modifiés, référence inchangée et poids sauvegardés vérifiés. La comparaison commune v28 est terminée : SFT et DPO 1/18 JSON conforme chacun dans le runtime Transformers FP4 ; aucun gain de triage DPO. Le runtime de démonstration sera évalué directement via vLLM/API ; aucun diagnostic autonome supplémentaire n’est un préalable. Validation clinique absente.

1. **Acquis :** corpus corrigé, SFT 500, DPO v27 et comparaison commune v28. Conserver les résultats négatifs ; aucun nouveau SFT long décidé.
2. **En cours :** vérifier vLLM et l’API avec les deux adaptateurs sur 18 scénarios synthétiques. La v30 a échoué à la liaison CUDA après chargement du modèle ; la v31 teste le correctif. Mesurer réponses, erreurs, latence et audit, puis vérifier la persistance après redémarrage.
3. **À réaliser :** figer le protocole et le runtime, puis exécuter une fois l’évaluation finale sur le test réservé. Les scripts de sélection, export et vérification existent ; ils ne constituent pas des résultats mesurés.
4. **À concrétiser :** cible cloud, accès et coût autorisés ; exécution GitHub Actions et déploiement de démonstration. Le quota Kaggle gratuit privé reste la seule autorisation GPU actuelle. Une API accessible seulement en boucle locale dans Kaggle ne remplit pas à elle seule ce livrable.
5. **À finaliser :** rapport PDF de 20 pages maximum et soutenance à partir des preuves obtenues. Le brouillon PDF existe ; la démonstration réelle reste à exécuter.

## Limites à garder visibles

Les 15 QCM et 30 générations déjà observés ne suffisent pas à conclure à une amélioration générale. Le test final reste isolé. Les scénarios synthétiques et seuils proposés ne sont pas une validation clinique. Le niveau de validation clinique attendu par l'école doit être clarifié avec le mentor, sans confondre cette question et les tâches techniques réalisables.

Le raccord DPO utilise désormais un manifeste du checkpoint et de son tokenizer au lieu d'un hash v5 codé en dur. Le checkpoint 500 a été rechargé fidèlement dans v25 ; le DPO v27 est exécuté et sa sauvegarde vérifiée. La comparaison v28 ne démontre pas de gain de triage après DPO.

## Historique

Les essais et décisions antérieurs restent dans l'[historique du projet](HISTORIQUE_PROJET_2026-09-11.md), les [preuves](../evidence/) et les [décisions](../decisions/). Cette page remplace l'accumulation de statuts historiques contradictoires ; elle décrit uniquement le travail courant.
