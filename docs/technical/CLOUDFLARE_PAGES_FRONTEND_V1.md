# Frontend Cloudflare Pages v1

- Date : 2026-09-16
- Statut : `frontend_deployed_backend_wiring_pending`
- Sources : [ADR-021](../decisions/ADR-021-separer-frontend-cloudflare-backend-modal.md),
  documentation Cloudflare citée dans l'ADR.

## Architecture

```text
Navigateur
  -> https://triage-poc.pierrepluton.com
  -> Cloudflare Pages : HTML, CSS, JavaScript
  -> Pages Functions GET /v1/healthz puis POST /v1/triage
  -> Modal : FastAPI + vLLM + Qwen3-1.7B SFT v39
  -> volume d'audit privé
```

Le build copie les actifs versionnés de `src/triage_poc/demo_ui/` vers
`deploy/cloudflare_pages/dist/`. Il ajoute une page de contrat, des en-têtes de sécurité et
deux routes Function. `_routes.json` évite d'invoquer la Function pour les actifs
statiques. Le dossier `dist/` et les secrets locaux restent hors Git.

## Contrat du proxy

La Function de santé accepte uniquement `GET /v1/healthz`. Le frontend l'interroge toutes les
5 secondes pendant au plus 130 secondes et n'envoie aucune donnée clinique avant que Modal
soit prêt. La Function de triage accepte uniquement `POST /v1/triage`,
`Content-Type: application/json`, un corps
d'au plus 32 Kio et un Bearer token égal au secret `DEMO_ACCESS_TOKEN`. La comparaison passe
par deux empreintes SHA-256 et `crypto.subtle.timingSafeEqual`. La destination doit être HTTPS
et se terminer par `.modal.run` ou `.modal.direct`. Le proxy remplace le jeton public par `MODAL_API_TOKEN`,
retourne le flux de réponse sans le journaliser et impose `Cache-Control: no-store`.

Variables et secrets à configurer après création de l'endpoint Modal :

| Nom | Type | Rôle |
|---|---|---|
| `MODAL_API_URL` | variable | origine HTTPS du serveur Modal |
| `MODAL_API_TOKEN` | secret | authentification entre Cloudflare et FastAPI |
| `DEMO_ACCESS_TOKEN` | secret | accès temporaire remis au jury |

## Commandes locales

```bash
cd deploy/cloudflare_pages
npm ci
npm audit --audit-level=high
npm run build:upload
npm run dev -- --ip 127.0.0.1 --port 8788
```

Le déploiement GitHub Actions reste manuel, exige `confirm_deploy=true` et l'environnement
`cloudflare-demo`. Il requiert `CLOUDFLARE_ACCOUNT_ID` et `CLOUDFLARE_API_TOKEN`. Le token doit
être limité au compte Pierre et à l'édition de Pages ; sa création et son enregistrement dans
GitHub sont des opérations séparées à confirmer.

## État de preuve

Le 16 septembre, le build Wrangler 4.132.0 compile, `npm audit` retourne zéro vulnérabilité,
22 tests ciblés passent et le runtime local retourne 200 pour la page, 401 pour un mauvais
jeton et 405 pour une méthode non autorisée. Le projet Cloudflare `chsa-triage-poc` est publié
sur `https://triage-poc.pierrepluton.com` ; la page, le contrat, les en-têtes et le certificat
ont été observés depuis l'extérieur. La [preuve de déploiement](../evidence/CLOUDFLARE_PAGES_DEPLOYMENT_2026-09-16.md)
sépare cette réussite du raccord Modal encore absent. Le backend Modal est désormais déployé
et vérifié séparément ; l'injection des trois valeurs Cloudflare et le smoke public restent à
effectuer.
