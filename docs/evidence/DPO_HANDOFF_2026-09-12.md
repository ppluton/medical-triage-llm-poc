# Raccord du checkpoint courant au DPO

- Date : 2026-09-12
- Statut : draft — vérification locale effectuée, entraînement DPO non lancé
- Sources : [audit de mission](AUDIT_ALIGNEMENT_MISSION_2026-09-12.md), [archive SFT](SFT_V22_CHECKPOINT_ARCHIVE_2026-09-12.json), [identité retenue](../../configs/sft-v22-handoff.json), [comparaison convertie](SFT_V22_DPO_COMPARISON_2026-09-12.json), [longueurs DPO](DPO_PREFLIGHT_LENGTHS_2026-09-12.json).
- Environnement : macOS, worktree `codex/complete-poc-evaluation`, Python du projet principal avec `PYTHONPATH=src`.

## Changement et preuve

Le runner ne dépend plus du hash SFT v5. Il reçoit `--sft-manifest` et vérifie les poids, la configuration de l'adaptateur, le tokenizer et le chat template avant tout chargement de modèle. La base et sa révision sont prises dans ce manifeste ; la comparaison doit concerner exactement les mêmes poids. Les contrôles de revue des données, confidentialité et isolation restent actifs.

Les cinq fichiers du checkpoint général v22 à 500 étapes correspondent aux hashes de l'archive déjà conservée. Le tokenizer local se charge et rend les prompts DPO. Les 512 paires train et 64 validation existantes respectent les plafonds de 1 024 tokens pour le prompt et 2 048 pour chaque séquence complète ; maxima complets respectifs : 1 639 et 1 116 tokens. Aucune troncature n'a été appliquée.

La comparaison au format attendu par DPO est dérivée des mesures v22 existantes. Son lien au résumé GPU et au hash des poids a été contrôlé ; aucune nouvelle inférence ni nouvelle mesure de qualité n'a été faite. Ce document ne constitue pas la décision d'acceptation DPO.

Tests ciblés : `PYTHONPATH=src python -m pytest tests/test_dpo.py -q` : **5 passed**. Ils couvrent identité du checkpoint et du tokenizer, nouvelle identité SFT acceptée, comparaison d'un autre checkpoint refusée, fuite de prompts et données non revues refusées. `ruff check src/triage_poc/dpo.py scripts/run_dpo.py tests/test_dpo.py` : succès.

## Commande après finalisation de la revue

```sh
PYTHONPATH=src python scripts/run_dpo.py \
  --sft-manifest configs/sft-v22-handoff.json \
  --sft-adapter artifacts/kaggle/continuation-v22-reports/source-sft-v2-continuation-500/trainer/checkpoint-500 \
  --comparison docs/evidence/SFT_V22_DPO_COMPARISON_2026-09-12.json \
  --dataset /absolute/path/to/reviewed-dpo \
  --decision /absolute/path/to/comparison-review.json \
  --output /absolute/path/to/fresh-dpo-output \
  --max-steps 20 --dry-run
```

Les chemins de dataset revu et de décision sont volontairement des paramètres, pas des approbations créées artificiellement. Le lot existant reste candidat. L'essai GPU, la référence gelée pendant l'entraînement, la sauvegarde/recharge DPO et l'effet sur les réponses ne sont pas prouvés par les vérifications locales ci-dessus. Le checkpoint 500 reste un candidat expérimental, pas un choix déclaré optimal ni cliniquement validé.

## Revue descriptive du lot existant

Le [contrôle complémentaire](DPO_CANDIDATE_REVIEW_2026-09-12.json) vérifie à nouveau les 512/64 paires contre les hashes de prompts protégés, sans lever l'exigence de revue de confidentialité. Le lot est entièrement anglais. Les étiquettes source du train sont `length=206`, `easy=105`, `hard=201` ; celles de validation sont `length=29`, `easy=10`, `hard=25`.

Dans 358/512 paires train et 41/64 paires validation, la réponse préférée est plus longue en caractères. Ce constat ne démontre ni biais causal ni supériorité de contenu. La lecture exploratoire d'une paire par type et par split montre des questions de connaissances, des cas cliniques et des sujets biologiques généraux. Certaines paires donnent le même choix final avec des explications différentes. Il serait donc incorrect de traduire systématiquement `chosen/rejected` par « décision de triage correcte/incorrecte » ou de promettre des réponses plus courtes après DPO. La revue exploratoire ne vaut pas validation exhaustive des 576 préférences.
