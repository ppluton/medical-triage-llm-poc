# ADR-021 — Séparer le frontend Cloudflare Pages du backend GPU Modal

- Date : 2026-09-16
- Statut : `approved`
- Propriétaire : Pierre
- Statut clinique : non applicable ; aucune validation clinique
- Sources : [Cloudflare Pages Functions](https://developers.cloudflare.com/pages/functions/),
  [secrets Pages](https://developers.cloudflare.com/pages/functions/bindings/),
  [déploiement direct](https://developers.cloudflare.com/pages/get-started/direct-upload/),
  [domaines personnalisés](https://developers.cloudflare.com/pages/configuration/custom-domains/)

## Contexte

Servir l'interface depuis le même conteneur Modal que vLLM réveillerait potentiellement le
GPU pour une simple consultation de page. GitHub Pages ne peut pas conserver le jeton du
backend côté serveur. Le POC doit limiter les crédits, ne publier aucun secret et conserver
une URL stable pour le jury.

## Décision

Le frontend statique et un proxy minimal sont déployés dans le projet Cloudflare Pages
`chsa-triage-poc`, avec le domaine cible `triage-poc.pierrepluton.com`. Le navigateur appelle
uniquement `POST /v1/triage` sur la même origine. La Pages Function vérifie un jeton d'accès
de démonstration, borne le corps à 32 Kio, puis transmet la requête au domaine Modal
`.modal.run` avec un jeton backend distinct conservé comme secret Cloudflare.

Le frontend, le proxy et le backend n'acceptent que des scénarios synthétiques pour cette
démonstration. Le proxy ne journalise ni corps, ni jeton. Les actifs statiques ne réveillent
pas Modal ; seule une requête d'inférence peut consommer des crédits GPU.

## Conséquences et limites

- `DEMO_ACCESS_TOKEN`, `MODAL_API_TOKEN` et `MODAL_API_URL` ne sont jamais intégrés au build.
- Le frontend peut être publié avant Modal ; `/v1/triage` répond alors explicitement `503`.
- Cloudflare constitue un nouveau sous-traitant technique du parcours de démonstration ; les
  données réelles restent interdites et la politique de conservation doit le mentionner.
- Une page accessible ne prouve ni endpoint Modal, ni vLLM, ni audit distant, ni sûreté
  clinique. Ces preuves restent séparées.
