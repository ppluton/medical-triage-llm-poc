# File de rédaction SFT gouvernée v1

- **Date :** 2026-08-31
- **Statut :** implemented
- **Sources :** spécification du POC, `configs/sft_authoring_queue.json`, manifestes MedQuAD, MEDIQA 2019 et FrenchMedMCQA, ADR-003 et ADR-004

## Objectif et périmètre

Le pipeline prépare exactement 5 000 candidats bilingues source-grounded pour une rédaction clinique ultérieure. Il ne produit aucun enregistrement conforme au contrat SFT final et ne rend aucune ligne entraînable.

UltraMedical-Preference est volontairement absent : cette source reste réservée à la préparation DPO. Les exports `test` de MEDIQA et FrenchMedMCQA sont exclus. MedQuAD ne fournit pas de split officiel utilisable pour le triage ; ses ancrages servent uniquement de références documentaires.

## Contrats et artefacts

| Artefact | Rôle |
|---|---|
| `configs/sft_authoring_queue.json` | quotas, volume, langues et portes fail-closed |
| `data/manifests/sft_authoring_candidate_v1.schema.json` | schéma d'un candidat non entraînable |
| `src/triage_poc/sft_authoring_queue.py` | sélection, déduplication, anonymisation et construction |
| `scripts/prepare_sft_authoring_queue.py` | génération, validation, index, lots et manifeste |
| `data/manifests/derived-sft-authoring-queue-v1.json` | compteurs, hashes et limites sans texte source |
| `data/processed/sft-authoring-queue-v1/` | file, index et 50 lots locaux hors Git |

## Quotas versionnés

- Langues demandées : 2 500 `fr`, 2 500 `en`.
- Ancrages documentaires : 1 000 MedQuAD, 750 MEDIQA, 750 FrenchMedMCQA.
- Candidats par source : 2 000, 1 500 et 1 500, car chaque ancrage crée une paire bilingue.
- Familles de rédaction : 600 douleur thoracique, 600 détresse respiratoire, 600 déficit neurologique, 560 pédiatrie, 560 grossesse, 560 vulnérabilité, 560 informations insuffisantes, 480 informations contradictoires et 480 autres.

Ces familles sont des quotas de travail `proposed_authoring_quota_only`. Elles ne décrivent pas le contenu clinique de la source et ne sont jamais transformées automatiquement en `triage_level`.

## Algorithme

1. Énumérer les ancrages autorisés de chaque source.
2. Exclure les réponses MedQuAD retirées en amont et les splits de test disponibles.
3. Ordonner les ancrages par SHA-256 stable de leur identité source.
4. Dédupliquer les questions par normalisation NFKC, casse et caractères non alphanumériques.
5. Borner chaque question et réponse source à 4 000 caractères.
6. Exécuter Presidio dans la langue source, remplacer les entités détectées, puis rechercher les résidus.
7. Rejeter tout résultat autre que `passed` et poursuivre jusqu'au quota.
8. Produire deux tâches par ancrage, FR et EN, avec tous les champs cliniques à `null`.
9. Valider chaque ligne contre le schéma, écrire la file JSONL, l'index sans texte et 50 lots de 100.
10. Calculer les SHA-256 et produire le manifeste dérivé.

## Commande reproductible

```bash
PYTHONPATH=src .venv/bin/python scripts/prepare_sft_authoring_queue.py \
  --medquad-repository data/raw/medquad \
  --mediqa-repository data/raw/mediqa2019 \
  --frenchmedmcqa-rebuilt data/processed/frenchmedmcqa-rebuilt \
  --output-directory data/processed/sft-authoring-queue-v1 \
  --schema data/manifests/sft_authoring_candidate_v1.schema.json \
  --config configs/sft_authoring_queue.json \
  --manifest-output data/manifests/derived-sft-authoring-queue-v1.json \
  --code-revision facd3e4 \
  --run-id sft-authoring-queue-2026-08-31 \
  --batch-size 100
```

Prérequis : environnement Python du projet, Presidio, `fr_core_news_md`, `en_core_web_sm` et sources locales aux révisions manifestées.

## Entrée, sortie et passage vers le SFT

La sortie conserve les extraits anonymisés nécessaires à la rédaction uniquement dans `data/processed/`, exclu de Git. L'index sans texte conserve les identifiants, groupes, sources, quotas et empreintes.

Une ligne ne pourra être convertie vers `triage_record_v1.schema.json` qu'après : rédaction d'un contexte synthétique, justification de la cible, revue de pertinence source, revue PII humaine, revue de sûreté, approbation clinique, puis assignation de split par groupe de scénario. Le convertisseur SFT existant doit continuer à refuser cette file.

## Limites

- Les remplacements automatiques comportent des faux positifs possibles sur des termes médicaux.
- Les 58 extraits tronqués nécessitent une attention particulière lors de la revue.
- La déduplication ne trouve pas les paraphrases sémantiques.
- Le volume de 5 000 tâches ne préjuge pas du nombre final d'exemples approuvés.
- Aucun résultat ne prouve la sûreté clinique, la qualité d'un futur modèle ni l'autorisation d'entraîner.
