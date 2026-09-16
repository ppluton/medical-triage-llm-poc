# ADR-020 — Réactiver Modal avec un budget strictement borné

- Date : 2026-09-16
- Statut : `approved`
- Propriétaire : Pierre
- Statut clinique : non applicable ; aucune validation clinique
- Sources : [tarifs Modal](https://modal.com/pricing),
  [budgets Modal](https://modal.com/docs/guide/budgets),
  [déploiement continu](https://modal.com/docs/guide/continuous-deployment),
  [serveurs Modal](https://modal.com/docs/guide/servers)

## Contexte

L'étape 3 exige simultanément un endpoint pilote, vLLM/FastAPI dans un conteneur et un
déploiement automatisé par GitHub Actions. La démonstration Kaggle + Quick Tunnel respecte
la dépense nulle, mais son URL est éphémère et son démarrage reste interactif : elle ne suffit
donc pas comme preuve de CD.

Pierre dispose désormais d'un workspace Modal Starter avec 30 USD de crédits mensuels. Le
16 septembre 2026, avant toute création de ressource, le portail a confirmé 0 USD consommé,
une limite d'usage totale ramenée à 5 USD et une limite de dépense nette fixée à 0 USD.

## Décision

Modal redevient la cible pilote principale sous les contraintes cumulatives suivantes :

1. T4, `min_containers=0`, `max_containers=1` et extinction après 120 secondes ;
2. limite fournisseur de 5 USD d'usage total pour la démonstration du jour ;
3. limite de 0 USD de charges hors crédits ;
4. workflow GitHub Actions uniquement manuel, avec confirmation booléenne et environnement
   protégé `modal-demo` ;
5. modèle Base et adaptateur SFT vérifiés par checksum avant ouverture de l'API ;
6. Bearer token séparé des identifiants Modal ;
7. scénarios synthétiques uniquement, puis récupération de l'audit et arrêt vérifié.

L'[ADR-021](ADR-021-separer-frontend-cloudflare-backend-modal.md) complète cette décision :
Cloudflare Pages sert l'interface et garde le jeton Modal dans une Function ; Modal ne reçoit
que les appels de triage et ne sert plus de point d'entrée statique principal.

La limite d'usage pourra être relevée explicitement pour la soutenance, sans modifier la
limite de dépense nette. Aucun relèvement automatique n'est autorisé.

## Conséquences et limites

- L'ADR-019 reste le plan de secours gratuit si Modal est indisponible.
- Les volumes persistants peuvent continuer à générer des frais de stockage après l'arrêt
  des workloads. Ils doivent être inventoriés après la démonstration et supprimés après
  récupération des preuves, sur autorisation distincte.
- Les 30 USD sont un crédit fournisseur, pas une garantie de gratuité sans les plafonds.
- Le workflow préparé ne prouve une CD qu'après une exécution GitHub observée.
- Un endpoint fonctionnel ne prouve ni sûreté clinique, ni aptitude aux données réelles.
