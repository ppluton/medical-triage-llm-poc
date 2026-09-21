# Préflight Cloudflare Pages — 16 septembre 2026

- Statut : `observed_local_and_upload_ready`
- Révision : `3c16e114fe84d6be77e5cefb0848c3a3617c568a`
- Données : scénarios synthétiques uniquement ; aucune donnée patient

## Résultats observés

- Wrangler local : `4.132.0` ; compilation de la Pages Function réussie.
- `npm audit --audit-level=high` : zéro vulnérabilité connue.
- Tests ciblés : 20 réussis, deux avertissements Starlette préexistants.
- `GET /` local : HTTP 200 avec CSP, `no-store`, `nosniff` et refus d'intégration en frame.
- `POST /v1/triage` avec mauvais jeton : HTTP 401, sans appel backend.
- `GET /v1/triage` : HTTP 405.
- Paquet Cloudflare : sept fichiers, 53 Ko, aucun secret ni jeton de test.
- Tableau de bord : compte Cloudflare du projet, projet `chsa-triage-poc`, paquet chargé
  avec `7/7 files uploaded` avant l'action finale de publication.

## Limites de la preuve

Ce préflight ne prouve pas encore l'URL `pages.dev`, le certificat du sous-domaine, les
secrets Cloudflare, le proxy vers Modal, le modèle réel, l'audit distant ou la CI/CD exécutée.
Ces preuves doivent être ajoutées uniquement après observation sur les services concernés.
