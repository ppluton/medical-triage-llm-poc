# Déploiement Cloudflare Pages — 16 septembre 2026

- Statut : `public_end_to_end_verified`
- Compte Cloudflare observé : `Pierre.pluton@outlook.fr`
- Projet Pages : `chsa-triage-poc`
- Révision du frontend/proxy/backend : `1590a110def2ac1d31ef97f251969e0a73fad101`
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
| mauvais Bearer token sur `/v1/healthz` et `/v1/triage` | HTTP 401 |
| bon token sur `/v1/healthz` | HTTP 200 après réveil Modal |
| scénario douleur thoracique FR | `maximum`, garde-fou v3, 34 984,70 ms |
| scénario déficit neurologique EN | `maximum`, garde-fou v3, 29 567,75 ms |
| Certificat TLS | CN et SAN `triage-poc.pierrepluton.com`, Google Trust Services WE1 |

Lors du premier contrôle, le site était déjà joignable en HTTPS tandis que le tableau de bord
affichait encore `Verifying`. Après propagation et actualisation, le statut fournisseur est
passé à `Active`. L'accès public, le certificat et l'activation Cloudflare sont donc observés.

## Incident de raccord et correction

Le premier raccord échouait en 502. Les logs temps réel Cloudflare ont montré que le runtime
Edge refuse `fetch(..., {redirect: "error"})`. Le proxy utilise désormais `redirect: "manual"`
et rejette explicitement tout statut 3xx. Les réponses JSON amont sont tamponnées avant retour.
Le même chemin a ensuite produit 200 sur la santé et deux réponses de triage contrôlées.

Les interactions `fcd6ffaf-6ad8-468d-83ef-5f5111fd311f` et
`f0334a77-5024-47ac-ab89-b7e80604bab3` ont été rapprochées du volume d'audit privé. Leur
statut de confidentialité vaut `passed`; leur statut clinique reste explicitement
`schema_validated_not_clinically_validated`.

## CI et limites

Les jobs GitHub `test` et `container` de la PR #4 sont passés sur le commit `35b2ad1`. Le
workflow Cloudflare manuel est versionné mais n'a pas encore été exécuté : les déploiements
observés ont été réalisés par Direct Upload. `DEMO_ACCESS_TOKEN` et `MODAL_API_TOKEN` sont
chiffrés côté Cloudflare ; leur valeur n'est ni versionnée ni reproduite ici. Le frontend
attend jusqu'à 190 secondes car deux cold starts publics ont pris 111 et 117,5 secondes.
Cette preuve établit le chemin pilote public et la persistance d'audit sur deux cas
synthétiques ; elle ne constitue ni un benchmark en charge ni une validation clinique.
