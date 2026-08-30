# Reconstruction UltraMedical-Preference v1

- **Date :** 2026-08-31
- **Statut :** implemented and observed
- **Sources :** `src/triage_poc/ultramedical_rebuild.py`, `scripts/rebuild_ultramedical_splits.py`, ADR-005

## Objectif

Produire une décision traçable pour chaque ligne des trois splits sans recopier les prompts et les réponses. L'index permet ensuite de relire uniquement les lignes candidates depuis la source épinglée.

## Algorithme

1. Lire en flux le test et calculer ses hashes de prompts normalisés.
2. Lire `dev`, retirer les hashes du test et protéger les hashes de validation restants.
3. Parcourir `train`, `dev` et `test` en conservant l'index source de chaque ligne.
4. Calculer un hash de groupe de prompt et un hash de préférence complète.
5. Appliquer la priorité `test > dev > train`.
6. Exclure les préférences exactement dupliquées dans `train` et `dev`.
7. Écrire un JSONL sans texte contenant la décision, les hashes et le statut de revue clinique.

## Contrat de sortie

Chaque ligne contient :

- `source_manifest_id` ;
- `source_split` et `source_row_index` ;
- `prompt_group_sha256` et `preference_sha256` ;
- `duplicate_preference_in_source_split` ;
- `decision` ;
- `clinical_review_status`.

Les décisions `candidate_training` et `candidate_validation` ne signifient pas `approved`. Elles signifient seulement que la ligne a passé la reconstruction textuelle exacte.

## Reproductibilité

```bash
PYTHONPATH=src .venv/bin/python scripts/rebuild_ultramedical_splits.py \
  data/raw/ultramedical-preference/data \
  data/processed/ultramedical-preference-reconstruction-index-v1.jsonl
```

Le manifeste dérivé versionné contient les comptes, la politique, la taille et le SHA-256 de l'index hors Git.

## Limites

Le hash de groupe repose sur une normalisation textuelle exacte ; il ne détecte pas les paraphrases. L'index ne fait aucun jugement clinique et ne prouve pas l'absence de PII. Une préparation DPO ultérieure doit relire les lignes candidates, appliquer l'anonymisation, la sélection spécifique au triage et la revue clinique.
