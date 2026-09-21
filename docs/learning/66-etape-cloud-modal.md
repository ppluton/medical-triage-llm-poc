# Préparer une démonstration GPU à coût borné

- Date : 2026-09-16
- Statut : `reactivated_with_budget_guardrails` par
  [ADR-020](../decisions/ADR-020-reactiver-modal-budget-borne.md)
- Sources : documentation Modal officielle citée dans
  `docs/technical/MODAL_DEPLOYMENT_V1.md`, preuves v37, sélection v43 et réserve v46.

## Ce qui a été fait

La cible Modal a été préparée puis déployée. La définition assemble vLLM et l'API dans le
même conteneur GPU tout en gardant leurs environnements Python séparés, monte les poids depuis
un volume privé et persiste l'audit dans un autre volume. Elle vérifie les checksums avant le démarrage, limite l'autoscaling à un conteneur et
revient à zéro après inactivité. Un workflow GitHub manuel et deux scénarios de smoke test
synthétiques complètent la préparation.

Le chemin public final utilise une Web Function Modal `.modal.run`, compatible avec le proxy
Cloudflare. Deux cold starts ont pris environ deux minutes. Les scénarios thoracique FR et
neurologique EN ont ensuite été exécutés depuis le frontend public et rapprochés de l'audit.

## Pourquoi cette étape est nécessaire

Une image locale, un notebook Kaggle ou un endpoint sur `localhost` ne prouvent pas que le
jury peut joindre l'application. Inversement, une URL HTTP 200 ne prouve ni le chargement du
bon modèle, ni l'audit, ni la sûreté clinique. La préparation sépare donc identité des poids,
service distant, authentification, persistance, smoke test et décision clinique.

## Notions à retenir

- `min_containers=0` permet le retour à zéro, mais ne fixe pas à lui seul un budget financier ;
- un volume de poids évite le téléchargement du modèle à chaque démarrage froid ;
- séparer les environnements vLLM et API évite qu'une mise à jour FastAPI/Presidio casse le runtime GPU ;
- les poids sont montés en lecture seule alors que l'audit exige un volume inscriptible ;
- le SFT v39 est le seul adaptateur servi, conformément à la sélection antérieure à la réserve ;
- le Bearer token de l'API n'est pas le token de déploiement Modal ;
- une CD manuelle et protégée reste une CD vérifiable sans déclencher des dépenses à chaque push.
- pour un signal d'alerte proposé, une priorité correcte ne suffit pas : le texte libre doit
  aussi être remplacé par une formulation déterministe qui ne suggère jamais d'attendre ;
- un cold start doit être mesuré sur le vrai chemin public avant de choisir le délai du frontend.

## Évolution de la décision

Pierre a d'abord exclu toute dépense et l'ADR-019 a retenu Kaggle + Quick Tunnel. Après
constat que cette voie ne prouvait pas la CD demandée, un compte Starter a été créé. Avant
toute ressource, l'usage total a été borné à 5 USD de crédits et la dépense nette à 0 USD.
Modal redevient la cible pilote ; Kaggle reste le secours éphémère.

L'[ADR-021](../decisions/ADR-021-separer-frontend-cloudflare-backend-modal.md) sépare ensuite
le frontend : Cloudflare Pages sert l'interface sans réveiller le GPU, tandis que sa Function
protégée appelle Modal uniquement lors d'une évaluation.

La démonstration ne doit pas prendre la forme d'un chat libre. Le produit combine un
formulaire initial court et une conversation guidée : l'API nomme le champ manquant, le
client range la réponse dans ce champ et renvoie le contexte consolidé. Ce choix conserve la
validation de schéma, distingue inconnu/absent/indisponible et rend chaque tour auditable.
