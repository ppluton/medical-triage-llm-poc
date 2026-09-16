# Déploiement Cloudflare Pages — 16 septembre 2026

- Statut : `frontend_deployed_backend_pending`
- Compte Cloudflare observé : `Pierre.pluton@outlook.fr`
- Projet Pages : `chsa-triage-poc`
- Révision du frontend/proxy : `3c16e114fe84d6be77e5cefb0848c3a3617c568a`
- Révision documentaire et workflow : `35b2ad107bf0ef21f196757c1301873c2a987147`
- Données : scénarios synthétiques uniquement ; aucune donnée patient réelle

## Déploiement observé

Le tableau de bord Cloudflare a confirmé `Success! Your project is deployed to Region: Earth`
et l'URL `https://chsa-triage-poc.pages.dev/`. Le domaine personnalisé a ensuite créé un CNAME
proxifié de `triage-poc.pierrepluton.com` vers `chsa-triage-poc.pages.dev`.

## Smoke tests externes

| Vérification | Résultat observé |
|---|---|
| `GET https://chsa-triage-poc.pages.dev/` | HTTP 200 |
| `GET https://triage-poc.pierrepluton.com/` | HTTP 200 et interface rendue dans le navigateur |
| `GET /docs/` sur le domaine personnalisé | HTTP 200, contrat pédagogique affiché |
| En-têtes | CSP, `Cache-Control: no-store`, `Referrer-Policy: no-referrer`, `nosniff`, `DENY` |
| `GET /v1/triage` | HTTP 405, méthode refusée |
| `POST /v1/triage` avant secrets Modal | HTTP 503, backend non configuré |
| Certificat TLS | CN et SAN `triage-poc.pierrepluton.com`, Google Trust Services WE1 |

Lors du premier contrôle, le site était déjà joignable en HTTPS tandis que le tableau de bord
affichait encore `Verifying`. Après propagation et actualisation, le statut fournisseur est
passé à `Active`. L'accès public, le certificat et l'activation Cloudflare sont donc observés.

## CI et limites

Les jobs GitHub `test` et `container` de la PR #4 sont passés sur le commit `35b2ad1`. Le
workflow Cloudflare manuel est versionné mais n'a pas encore été exécuté : le premier
déploiement a été réalisé par Direct Upload. Les secrets `DEMO_ACCESS_TOKEN`,
`MODAL_API_TOKEN` et `MODAL_API_URL` ne sont pas configurés. Cette preuve établit le frontend
public, pas l'inférence vLLM, la latence GPU, la persistance d'audit ou une validation clinique.
