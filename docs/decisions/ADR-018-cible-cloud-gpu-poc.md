# ADR-018 — Cible GPU cloud du POC

- Date : 2026-09-16
- Statut : `superseded` par [ADR-019](ADR-019-demonstration-zero-cout.md)
- Propriétaire : Pierre
- Statut clinique : non applicable ; aucune validation clinique
- Sources : [tarifs Modal](https://modal.com/pricing), [GPU Modal](https://modal.com/docs/guide/gpu), [endpoints Modal](https://modal.com/docs/guide/dedicated-endpoints), [tarifs RunPod](https://www.runpod.io/pricing), [GPU Spaces Hugging Face](https://huggingface.co/docs/hub/spaces-gpus), [Docker Spaces](https://huggingface.co/docs/hub/main/en/spaces-sdks-docker)

## Contexte

Le livrable demande un endpoint cloud accessible pour la démonstration, avec vLLM, l’API
FastAPI, un accès restreint, les garde-fous et l’audit. Le dépôt possède déjà une image API et
un `compose.demo.yaml` séparant vLLM et FastAPI. Aucun compte GPU cloud, budget ni cible de
déploiement n’est actuellement autorisé. Le projet Railway observé appartient à LGDM et ne
doit pas être réutilisé.

Le modèle de 1,7 milliard de paramètres et ses adaptateurs tiennent sur une carte de 16 à
24 Go pour cette démonstration bornée. Ce constat technique ne constitue pas encore une
mesure de capacité ou de latence sur le fournisseur final.

## Options vérifiées

### A — Modal avec extinction automatique

Modal facture la T4 `0,000164 USD/s`, soit environ `0,5904 USD/h` de GPU lorsqu’elle tourne,
auxquels s’ajoutent CPU et mémoire. Le plan Starter annonce 30 USD de crédit mensuel. Les
endpoints arrêtés à zéro ne génèrent pas de coût de calcul. Modal accepte des GPU T4/L4/A10 et
des poids personnalisés, mais impose d’adapter le démarrage vLLM/FastAPI et de transférer les
artefacts vers un volume ou un build privé Modal.

### B — RunPod

RunPod affiche un niveau Serverless 16 Go à `0,58 USD/h` pour un worker flexible et un niveau
24 Go à `0,69 USD/h`. Le Serverless peut revenir à zéro, mais son contrat de handler demande
une adaptation de l’API. Un Pod dédié accepte plus directement Docker et le compose existant ;
il faut alors piloter explicitement son arrêt et son stockage.

### C — Hugging Face Docker Space

Un Space Docker fournit directement une URL web. La T4 small est affichée à `0,40 USD/h` et
la facturation est calculée à la minute pendant les états `Starting` et `Running`. Un sommeil
peut arrêter le coût, au prix d’un démarrage à froid. La visibilité protégée — code privé mais
application accessible — dépend d’un plan payant, et le conteneur unique demande de réunir ou
superviser vLLM et FastAPI.

## Proposition historique

Cette proposition Modal n'est plus active. Pierre a fixé le 16 septembre 2026 une contrainte
de dépense nulle. L'[ADR-019](ADR-019-demonstration-zero-cout.md) retient donc une
démonstration éphémère Kaggle + Cloudflare, sans création de ressource Modal.

## Décision remplacée

La demande d'autorisation de budget est annulée. Les fichiers Modal sont conservés comme
travail technique historique, mais ne doivent pas être déployés dans le parcours sans coût.

## Conséquences

Après décision, l’implémentation doit :

1. conserver les poids et tokens hors Git ;
2. déployer l’API avec un Bearer token et HTTPS ;
3. exécuter un smoke test distant FR/EN avec entrées synthétiques ;
4. mesurer démarrage, p50/p95 et débit sur cette cible ;
5. vérifier l’audit anonymisé et la reprise ;
6. ajouter une CD ciblée sans rendre l’endpoint public par défaut ;
7. arrêter la ressource et vérifier l’arrêt de facturation après la soutenance.

Cette décision de fournisseur ne change ni les résultats du modèle ni son statut clinique.
