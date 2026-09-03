# Revue pilote SFT 001 v1

- **Date :** 2026-09-03
- **Statut :** implemented — décisions humaines non commencées
- **Sources :** file candidate v2, schéma `sft_review_item_v1`, manifeste `derived-sft-review-pilot-001-v1`

## Objectif

Préparer un paquet de revue représentatif avant toute rédaction SFT. Le paquet contient 50 ancrages documentaires, chacun relié aux deux tâches FR/EN du même groupe, soit 100 candidats de la file v2.

Le fichier local ne demande pas au réviseur d'attribuer immédiatement un niveau `maximum`, `moderate` ou `deferred`. Il vérifie d'abord si l'ancrage peut raisonnablement soutenir une rédaction, s'il conserve un risque de données personnelles et s'il correspond à la famille de travail demandée.

## Pourquoi `review-batch-001` a été remplacé pour le pilote

Le lot séquentiel généré avec la file v2 contient 100 candidats `chest_pain`. Son intégrité est correcte, mais il ne représente ni les huit autres familles ni la distribution globale des sources. Il reste un lot de production valide, mais ne doit pas servir de pilote général.

Le nouveau pilote utilise la méthode `proportional_largest_remainder_by_risk_family_and_source` sur les groupes bilingues complets. La seed `sft-review-pilot-v1` rend la sélection reproductible.

## Champs à compléter

Pour chaque groupe :

- `source_relevance_status` : l'ancrage contient-il une connaissance utile à la future rédaction ?
- `privacy_review_status` : le texte anonymisé peut-il rester dans le flux de travail ?
- `risk_family_alignment_status` : l'ancrage convient-il à la famille demandée ?
- `authoring_suitability_status` : un rédacteur peut-il produire un scénario sûr et cohérent à partir de cet ancrage ?
- `reviewer_role`, `reviewer_id`, `reviewed_at`, `notes` : traçabilité de la décision.

`clinical_validation_status` reste distinct. Une revue de pertinence documentaire effectuée par l'équipe technique ne vaut pas validation clinique.

## Commande reproductible

```bash
PYTHONPATH=src .venv/bin/python scripts/prepare_sft_review_pilot.py \
  --queue data/processed/sft-authoring-queue-v2/sft-authoring-queue-v2.jsonl \
  --queue-sha256 e4ac60c336aeb24dfb602f8e6f4539217f6f751239ac321946322a9ff68bdd9d \
  --candidate-schema data/manifests/sft_authoring_candidate_v1.schema.json \
  --review-schema data/manifests/sft_review_item_v1.schema.json \
  --output-directory data/processed/sft-review-pilot-v1 \
  --manifest-output data/manifests/derived-sft-review-pilot-001-v1.json \
  --group-count 50 \
  --seed sft-review-pilot-v1 \
  --code-revision 4fa05b1 \
  --run-id sft-review-pilot-001-2026-09-03
```

## Sortie et confidentialité

Le dossier local contient le contrat canonique `review-pilot-001.jsonl` et le tableur éditable `review-pilot-001.csv`. Ces deux fichiers contiennent les textes d'ancrage et restent hors Git. Seuls le schéma, le manifeste text-free, les compteurs et les checksums sont versionnés.

## Porte de sortie

Le pilote ne passe à la rédaction que lorsque les 50 groupes possèdent une décision traçable de pertinence, confidentialité, alignement et aptitude. Une décision clinique séparée reste nécessaire avant toute cible de triage ou utilisation d'entraînement.
