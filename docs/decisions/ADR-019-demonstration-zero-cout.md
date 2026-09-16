# ADR-019 — Démonstration extérieure sans dépense

- Date : 2026-09-16
- Statut : `approved`
- Propriétaire : Pierre
- Statut clinique : non applicable ; aucune validation clinique
- Sources : [Railway Plans](https://docs.railway.com/pricing/plans),
  [Cloudflare Workers AI Pricing](https://developers.cloudflare.com/workers-ai/platform/pricing/),
  [Cloudflare LoRA adapters](https://developers.cloudflare.com/workers-ai/features/fine-tunes/loras/),
  [Cloudflare Quick Tunnels](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/),
  [Kaggle Notebooks](https://www.kaggle.com/docs/notebooks)

## Contexte

Pierre exclut toute dépense pour le POC. Le service doit néanmoins démontrer la chaîne exacte
Qwen3-1.7B-Base + SFT v39 + vLLM + API, sans substituer un autre modèle au candidat évalué.

Le plan Railway Free fournit 0,5 Go de RAM, 1 vCPU, 1 Go de stockage éphémère et 1 USD de
crédit mensuel. Ces limites ne permettent pas de charger les 3,2 Gio du modèle, son cache et
vLLM. Railway pourrait héberger une façade CPU, mais ne résout pas le calcul GPU.

Workers AI accorde 10 000 neurons par jour sans frais et propose certains modèles Qwen.
Cependant, Qwen3-1.7B-Base ne figure pas parmi les bases LoRA prises en charge et l'import
LoRA documenté attend actuellement les familles `mistral`, `gemma` ou `llama`. Utiliser un
modèle Cloudflare différent invaliderait la comparaison Base/SFT/DPO déjà réalisée.

Kaggle fournit gratuitement une T4 temporaire déjà utilisée et vérifiée par ce projet.
Cloudflare Quick Tunnels fournit une URL HTTPS aléatoire gratuite vers un service local, avec
une limite documentée à la démonstration et sans garantie de disponibilité.

## Décision

La démonstration extérieure sans dépense utilise :

1. le notebook Kaggle privé et sa T4 gratuite pour vLLM ;
2. la ressource Kaggle privée et checksum-lockée pour Qwen3-1.7B-Base ;
3. uniquement l'adaptateur SFT v39 sélectionné ;
4. la factory FastAPI sur `127.0.0.1`, protégée par un Bearer token d'au moins 32 caractères ;
5. un Quick Tunnel Cloudflare éphémère vers l'API ;
6. un arrêt total quand la session Kaggle ou le lanceur s'arrête.

Railway n'est pas ajouté : une façade supplémentaire augmenterait le nombre de composants
sans fournir le GPU manquant. Modal, RunPod et les conteneurs Cloudflare payants restent hors
du parcours autorisé.

## Conséquences et limites

- L'URL change à chaque session et ne possède ni SLA ni disponibilité permanente.
- Le tunnel n'est pas un déploiement de production ni une preuve de CI/CD GPU.
- Le notebook doit rester actif pendant la démonstration et dépend du quota Kaggle.
- Seuls des scénarios synthétiques sont autorisés ; aucune donnée patient réelle.
- Le token ne doit apparaître ni dans Git, ni dans le manifeste d'endpoint, ni dans les logs.
- Le lanceur vérifie les checksums du modèle, de l'adaptateur et de `cloudflared` avant tout
  démarrage, puis vérifie `/healthz` localement et via l'URL publique.

Cette décision satisfait la contrainte financière et fournit une démonstration extérieure
temporaire. Elle ne satisfait pas une exigence de service permanent, de SLA ou de déploiement
hospitalier.
