# Reconstruction des splits UltraMedical-Preference

- **Date :** 2026-08-31
- **Statut :** proven for exact normalized overlap removal; not approved for DPO
- **Sources :** `data/manifests/derived-ultramedical-reconstruction-v1.json`, ADR-005, révision source `761eb7935310ba662a96d93c5af342e5269d5759`

## Claim vérifié

Le script doit produire un index sans texte source qui réserve le test, retire de `dev` les prompts présents dans le test, retire de `train` les prompts protégés par `test` ou `dev`, et exclut les préférences exactement dupliquées dans les splits candidats.

## Environnement et commande

- Python : environnement local `.venv`.
- Dépendance de lecture en flux : `ijson 3.5.1`.
- Code : branche `codex/sft-training-foundation`.

```bash
PYTHONPATH=src .venv/bin/python scripts/rebuild_ultramedical_splits.py \
  data/raw/ultramedical-preference/data \
  data/processed/ultramedical-preference-reconstruction-index-v1.jsonl
```

## Résultat observé

| Décision | Lignes |
|---|---:|
| `candidate_training` | 95 350 |
| `candidate_validation` | 2 227 |
| `reserved_evaluation` | 777 |
| `excluded_dev_overlap` | 1 688 |
| `excluded_test_overlap` | 55 |
| `excluded_exact_duplicate` | 12 265 |

- Prompts uniques conservés : 74 944 entraînement, 2 214 validation, 776 évaluation.
- Lignes source traitées : 109 353 `train`, 2 232 `dev`, 777 `test`.
- Index : 45 117 408 octets.
- SHA-256 : `6cfc7c8190e0d195354614b2a4b53684eb6e20155c9bf73684d99d6372dca58b`.
- Texte source dans l'index : non.

Les exclusions par chevauchement sont comptées en lignes, pas en prompts uniques : plusieurs préférences peuvent partager le même prompt.

## Ce que cela prouve et ne prouve pas

**Prouvé :** avec la normalisation documentée, les priorités `test > dev > train` et la déduplication exacte sont appliquées de façon déterministe ; l'index ne contient pas les prompts ni les réponses.

**Non prouvé :** l'absence de paraphrases entre splits, la pertinence des 95 350 paires candidates pour le triage, leur anonymisation complète, leur exactitude biomédicale ou leur validation clinique. Le statut reste `candidate_index_not_training_data`.

## Vérification automatisée

- Tests ciblés : 3 tests de priorité, déduplication et déterminisme.
- Suite complète à exécuter avant commit : `PYTHONPATH=src .venv/bin/python -m pytest -q`.
- Lint : `.venv/bin/python -m ruff check src tests scripts`.
