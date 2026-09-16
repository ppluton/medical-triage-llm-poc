# Preuve locale — build Docker

- **Statut :** proven_for_local_api_container
- **Date :** 2026-09-16

Docker 29.6.2 a construit l'image locale `medical-triage-poc:ci-local` sous Linux
arm64. Identité observée :

```text
sha256:13c3de41bd453deff19167c6c4e08e34c304f45d6a1ea8a45aba2cf2969e3be5
size: 213241461 bytes
```

Le premier job `val_f1d97c55a241` a échoué avant le build parce que le helper
`docker-credential-osxkeychain` n'était pas dans le `PATH` de Portly. Le second job
`val_0b32860bf240` a ajouté explicitement le répertoire officiel des binaires Docker
Desktop et s'est terminé avec le code 0.

Deux sondes ont été exécutées avec `--network none` :

1. application sans fournisseur : health `200`, triage `503` ;
2. factory privée avec variables synthétiques : health sans token `401`, health avec
   token `200`, `provider_configured=true`, `clinical_validation=not_performed`, et
   triage sans token `401`.

Cette preuve établit la construction locale et le câblage d'authentification de l'API.
Elle ne démarre pas vLLM, ne charge aucun modèle, ne réalise aucune inférence GPU et ne
prouve ni GitHub Actions ni un déploiement cloud.
