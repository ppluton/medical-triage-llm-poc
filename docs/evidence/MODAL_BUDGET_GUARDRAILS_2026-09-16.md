# Garde-fous budgétaires du pilote Modal

- Date : 2026-09-16
- Statut : `observed_provider_configuration_no_resources_created`
- Environnement : workspace Modal Starter `ppluton`
- Sources : [ADR-020](../decisions/ADR-020-reactiver-modal-budget-borne.md), portail Modal

## Observation

Avant toute création de volume, secret applicatif, image distante ou GPU, le portail Modal a
affiché :

- plan Starter avec 30 USD de crédits mensuels ;
- consommation courante de 0 USD ;
- limite de dépense nette enregistrée à 0 USD ;
- limite d'usage totale enregistrée à 5 USD, crédits inclus.

Le portail indique après enregistrement `$0 / $0 in charges` et `$0 / $5` pour l'usage du
cycle courant. Aucun identifiant de compte, jeton ou moyen de paiement n'est consigné ici.

## Ce que cela prouve et ne prouve pas

Cette observation prouve la configuration des deux plafonds avant le pilote. Elle ne prouve
pas encore la création des ressources, le démarrage de la T4, le fonctionnement de vLLM,
l'URL, la CD GitHub Actions ni l'absence absolue de frais de stockage. Modal avertit que les
volumes peuvent continuer à générer des frais ; leur inventaire et leur suppression après
récupération des preuves font partie de la procédure d'arrêt.
