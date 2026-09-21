# Déploiement continu observé par GitHub Actions — 21 septembre 2026

- Statut : `cd_workflows_verified_public_end_to_end`
- Workflows : `.github/workflows/deploy-modal.yml`, `.github/workflows/deploy-cloudflare-pages.yml`
- Environnements GitHub : `modal-demo`, `cloudflare-demo`, limités à la branche `main`, secrets chiffrés
- Données : scénarios synthétiques uniquement ; aucune validation clinique

## Question

Les workflows de déploiement versionnés peuvent-ils redéployer le backend Modal et le frontend Cloudflare
depuis `main`, sans poste de développement, puis servir le parcours public authentifié ?

## Exécutions retenues

| Workflow | Run | Révision | Résultat |
|---|---|---|---|
| Déploiement Modal | [35577931230](https://github.com/ppluton/medical-triage-llm-poc/actions/runs/35577931230) | `e9002c1` | succès ; cold start prêt en 155 s ; smoke 2/2 HTTP 200, 20,7 s et 37,2 s |
| Déploiement Cloudflare Pages | [35579884671](https://github.com/ppluton/medical-triage-llm-poc/actions/runs/35579884671) | `5ab90fc` | succès ; `npm audit` 0 vulnérabilité ; déploiement Production `main` |

Vérification publique après déploiement, GPU à zéro, sur `https://triage-poc.pierrepluton.com` :

- mauvais token : HTTP 401 ;
- sonde `/v1/healthz` : HTTP 524 à 125 s, puis 200 à 131 s ;
- `POST /v1/triage`, scénario synthétique FR : HTTP 200 en 34,4 s, niveau `maximum`, identifiant
  d'interaction présent, modèle `c911f9c6…` (SFT v39).

## Défauts trouvés et corrigés pendant la mise en service

| Symptôme | Cause | Correction |
|---|---|---|
| Smoke Modal en échec au 1er scénario | timeout client 90 s < cold start | [PR #9](https://github.com/ppluton/medical-triage-llm-poc/pull/9) : 190 s |
| Idem après redéploiement complet | Modal renvoie 303 au-delà de 150 s | [PR #10](https://github.com/ppluton/medical-triage-llm-poc/pull/10) : réveil par `/healthz` avant le smoke |
| Réveil bloqué sur 401 | `/healthz` protégé par le bearer token | [PR #11](https://github.com/ppluton/medical-triage-llm-poc/pull/11) : token envoyé, statuts du smoke journalisés |
| Validation wrangler en échec | clé `observability` refusée pour Pages | [PR #12](https://github.com/ppluton/medical-triage-llm-poc/pull/12) |
| Proxy 503 « backend not configured » | `MODAL_API_URL` était une variable projet écrasée par les `vars` du fichier wrangler | secret Pages `MODAL_API_URL` |
| Proxy 503 « no upstreams available » | URL régionale `modal.direct` de l'ancien déploiement | secret remplacé par l'URL `.modal.run` stable |
| Interface abandonnée pendant le cold start | 524/504 Cloudflare non réessayés | [PR #13](https://github.com/ppluton/medical-triage-llm-poc/pull/13) |

## Ce que cela prouve et ne prouve pas

La chaîne CD versionnée redéploie et vérifie les deux couches à partir de `main`, et le parcours public
authentifié fonctionne après un démarrage à froid. Cela ne prouve ni la tenue en charge, ni la qualité
clinique des réponses : la priorité observée provient des garde-fous déterministes décrits dans le rapport.
Le premier appel après inactivité reste long (environ deux minutes).
