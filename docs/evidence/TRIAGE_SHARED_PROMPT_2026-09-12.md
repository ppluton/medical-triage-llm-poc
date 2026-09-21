# Consigne de triage partagée entre évaluation et API

- Date : 2026-09-12
- Statut : draft — implémentation locale vérifiée, effet du prompt non mesuré sur GPU
- Sources : `configs/educational_triage_protocol_v1.json`, `src/triage_poc/triage_prompt.py`, `tests/test_serving.py`, `tests/test_triage_probe.py`.

## Changement et périmètre

La version `triage-demo-v3-proposed` explicite les définitions et la préséance des
niveaux du protocole pédagogique proposé existant. Elle ne crée pas de seuil clinique.
Elle demande de ne pas inventer de faits et de traiter les champs absents comme inconnus.
Le prompt inclut le schéma ModelResult et demeure identique entre transport API et
évaluation brute. L'API conserve son décodage contraint ; l'évaluation brute reste
sans correction des sorties. Ces deux modes doivent rester distingués dans les résultats.

Le runner archive désormais la version et le texte exact du prompt dans son résumé.
Le constructeur Kaggle inclut le nouveau module dans son paquet. Aucun notebook
n'a été lancé pour cette modification ; les mesures v25 restent historiques.

## Preuve locale

Environnement : macOS, branche `codex/complete-poc-evaluation`, Python 3.13 du venv
principal, import du worktree imposé par `PYTHONPATH=src`.

Commande : `PYTHONPATH=src .venv/bin/python -m pytest tests/test_triage_probe.py tests/test_serving.py -q`.

Résultat : 13 tests réussis en 6,52 s ; avertissement Starlette/httpx de dépréciation.
Ruff signale initialement deux ordres d'import, corrigés ; contrôle final réussi.

Le test de transport inspecte la véritable requête construite par VllmProvider avec
MockTransport et la compare au message de l'évaluateur. Le test des 18 scénarios
vérifie que modifier la référence attendue ne change pas le prompt. Les autres
contrôles conservent anonymisation simulée, audit sur fichier, refus des sorties
invalides et diagnostic de cache.

Prouvé : contrat local de transport partagé et absence de fuite de la référence
par scénario. Non prouvé : adhésion du modèle aux consignes, amélioration du triage,
compatibilité du serveur vLLM réel et validation clinique. Prochaine étape : mesure
commune Base/SFT puis DPO sans réutilisation du test final pour les ajustements.
