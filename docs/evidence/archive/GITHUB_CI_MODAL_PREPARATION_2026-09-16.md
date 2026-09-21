# CI GitHub après préparation Modal

- Date : 2026-09-16
- Statut : `passed`
- Dépôt : `ppluton/medical-triage-llm-poc`
- Branche : `codex/complete-poc-evaluation`
- Révision évaluée : `be42c0fbb3022bcd8c1203d3153812c15e3622ed`
- Pull request : [#4](https://github.com/ppluton/medical-triage-llm-poc/pull/4)
- Exécution : [GitHub Actions 35053173623](https://github.com/ppluton/medical-triage-llm-poc/actions/runs/35053173623)

Le job `container` passe en 42 secondes. Il construit l'image API et exerce hors réseau la
santé sans fournisseur, puis la factory authentifiée sans inférence. Le job `test` passe en
2 minutes 04 secondes : 240 tests, Ruff sur `src`, `scripts`, `tests` et `deploy`, puis lecture
de tous les manifestes JSON.

Cette preuve établit l'exécution distante de la CI et la construction du conteneur API pour
cette révision. Elle ne déclenche pas `.github/workflows/deploy-modal.yml`, qui reste manuel,
et ne prouve ni image Modal, ni GPU, ni endpoint, ni smoke test, ni qualité clinique.
