# Comprendre la démonstration extérieure à 0 €

- Date : 2026-09-16
- Statut : `draft`
- Sources : [ADR-019](../decisions/ADR-019-demonstration-zero-cout.md),
  [guide technique](../technical/DEMONSTRATION_KAGGLE_CLOUDFLARE_V1.md)

## Ce qui a été fait

La proposition de GPU Modal payant a été remplacée par un montage sans dépense : Kaggle
exécute le modèle sur sa T4 gratuite et Cloudflare rend temporairement l'API joignable depuis
Internet. Railway a été étudié mais écarté du chemin critique.

## Pourquoi

Un free tier « hébergement web » et un free tier « inférence GPU » ne sont pas équivalents.
Railway peut exécuter une petite application CPU, mais sa mémoire gratuite est inférieure au
seul poids du modèle. Workers AI fournit du GPU géré gratuitement dans une limite quotidienne,
mais pas notre base Qwen3-1.7B avec notre adaptateur. Remplacer le modèle aurait rendu les
résultats précédents incomparables.

## Comment

Le nouveau lanceur vérifie toutes les identités, démarre vLLM puis l'API en boucle locale,
ouvre un Quick Tunnel et vérifie la santé de l'URL extérieure. Le token reste un secret Kaggle.
Le tunnel et la session sont éphémères : c'est adapté à une soutenance, pas à un pilote réel.

## Notions à retenir

- L'URL publique n'est pas le calcul : Cloudflare transporte la requête, Kaggle l'infère.
- « Gratuit » implique ici quotas, démarrages manuels et absence de SLA.
- Une offre avec un autre modèle n'est pas un hébergement équivalent du modèle évalué.
- L'authentification reste obligatoire même pour une démonstration synthétique.

## Questions ouvertes

- Le quota GPU Kaggle sera-t-il disponible le jour de la soutenance ?
- L'exécution extérieure réelle et son smoke test restent à consigner.
- Une exigence stricte de CI/CD vers un GPU permanent ne peut pas être revendiquée à 0 € avec
  les offres vérifiées ici.
