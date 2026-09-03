# File de rédaction SFT gouvernée v2

- **Date :** 2026-09-03
- **Statut :** implemented
- **Sources :** `SPEC_POC_TRIAGE_MEDICAL.md`, ADR-006, manifestes MediQAl, MedQuAD et FrenchMedMCQA, `configs/sft_authoring_queue.json`

## Changement par rapport à v1

La v2 remplace `abachaa/MEDIQA2019` par la source prescrite `ANR-MALADES/MediQAl`. La v1 et sa preuve restent conservées comme historique. Les autres sources restent les versions canoniques déjà auditées : `abachaa/MedQuAD` et `qanastek/frenchmedmcqa`.

La sortie contient toujours exactement 5 000 candidats bilingues non entraînables : 2 000 MedQuAD, 1 500 MediQAl et 1 500 FrenchMedMCQA. UltraMedical-Preference reste réservé au DPO.

## Règles MediQAl

1. Lire uniquement `mcqu` et `mcqm`.
2. Sélectionner seulement `train` et `validation`.
3. Exclure les trois exports `test`, y compris OEQ.
4. Construire l'ensemble normalisé de toutes les questions de test.
5. Exclure toute question `train` ou `validation` qui recoupe cet ensemble.
6. Conserver le cas clinique et la question comme ancrage, puis résoudre les lettres `correct_answers` vers le texte des options.
7. Ne jamais interpréter une bonne réponse de QCM comme un niveau de triage.

## Commande reproductible

```bash
PYTHONPATH=src .venv/bin/python scripts/prepare_sft_authoring_queue.py \
  --medquad-repository data/raw/medquad \
  --mediqal-repository data/raw/mediqal \
  --frenchmedmcqa-rebuilt data/processed/frenchmedmcqa-rebuilt \
  --output-directory data/processed/sft-authoring-queue-v2 \
  --schema data/manifests/sft_authoring_candidate_v1.schema.json \
  --config configs/sft_authoring_queue.json \
  --manifest-output data/manifests/derived-sft-authoring-queue-v2.json \
  --code-revision 29c9af0 \
  --run-id sft-authoring-queue-v2-2026-09-03 \
  --batch-size 100
```

## Sorties

- `data/processed/sft-authoring-queue-v2/sft-authoring-queue-v2.jsonl` : contenu local hors Git ;
- `data/processed/sft-authoring-queue-v2/sft-authoring-index-v2.jsonl` : index local sans texte source ;
- 50 fichiers `review-batch-*.jsonl` de 100 lignes ;
- `data/manifests/derived-sft-authoring-queue-v2.json` : manifeste versionné, hashes et compteurs.

Les fichiers `review-batch-*.jsonl` sont des tranches séquentielles de production. Ils ne constituent pas automatiquement des échantillons représentatifs. Le pilote général utilise la sélection stratifiée décrite dans `REVUE_PILOTE_SFT_001_V1.md`.

## Limites

La file v2 ne contient toujours ni scénario patient final, ni réponse SFT, ni label de triage, ni split final. Presidio a rejeté les ancrages qui conservaient une détection résiduelle, mais une revue PII humaine reste nécessaire. Le filtre de fuite détecte les égalités normalisées, pas les paraphrases sémantiques.
