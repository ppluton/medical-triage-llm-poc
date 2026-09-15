# Corpus de l’étape 1 — état reproductible

Date : 2026-09-16 — Statut : draft, candidat technique ; portes clinique et RGPD ouvertes

Sources : [spécification d’exécution](../../SPEC_EXECUTION_V1.md), [registre des sources](../governance/REGISTRE_SOURCES_DONNEES.md), [manifeste SFT](../../data/manifests/derived-source-medical-qa-sft-v2.1-reviewed.json), [preuve datée](../evidence/AUDIT_CORPUS_ETAPE_1_2026-09-16.md).

## Objet

Cette page est l’entrée technique active pour le corpus demandé à l’étape 1. Elle décrit les artefacts existants sans convertir une revue automatique en validation clinique.

## Inventaire figé

| Source | Révision locale | Licence affichée | Format et langue | Rôle retenu |
|---|---|---|---|---|
| MediQAl | `5af34948a74c7b8807c476204a21149ffb00ea2c` | CC BY 4.0 | JSONL, français | QA/QCM SFT ; train MCQU/MCQM uniquement |
| FrenchMedMCQA | `be9a03fde01d9f05107b14941af1ad99897691cf` ; archive `58724c…` | Apache-2.0 | archive JSON, français | QA/QCM SFT ; splits projet reconstruits |
| MedQuAD | `577bd37b96c02d1833b2c9eed2de9f96964e96cb` | CC BY 4.0 | XML, anglais | QA SFT ; sous-ensembles 10–12 exclus |
| UltraMedical-Preference | `761eb7935310ba662a96d93c5af342e5269d5759` | MIT | tableaux JSON, anglais | préférences DPO ; splits reconstruits par groupe de prompt |

Les quatre manifestes `src-*` enregistrent URL, révision, licence, taille, empreinte et restrictions. Les pages amont et les révisions locales ont été revérifiées le 16 septembre ; cette revue ne remplace pas un avis juridique.

## Candidat SFT retenu

`derived-source-medical-qa-sft-v2.1-reviewed` contient **4 700 paires**, soit 3 721 train, 479 validation et 500 test. La répartition est 2 474 français / 2 226 anglais :

| Source | Enregistrements |
|---|---:|
| MediQAl | 1 475 |
| FrenchMedMCQA | 999 |
| MedQuAD | 2 226 |

Le canonique conserve la provenance de chaque ligne, les opérations de transformation, le statut d’anonymisation et le split. Les choix QCM sont rendus avant la réponse, les contenus trop longs sont exclus plutôt que tronqués et le test n’est pas rendu pour l’entraînement. Aucun `triage_label` n’a été inventé : ce corpus apprend de la QA médicale, pas une politique de priorité validée.

Les artefacts textuels restent hors Git public dans `data/processed/source-sft-v2.1-reviewed/`. Leurs SHA-256 et volumes sont consignés dans le manifeste versionné.

## Lot DPO disponible

`artifacts/dpo-reviewed-v1/` contient 426 paires train et 54 validation, toutes en anglais et issues d’UltraMedical-Preference. Les empreintes des deux JSONL correspondent au manifeste. Les lignes conservent le locator, la révision source, le type de préférence et les statuts de revue.

Ce lot n’est **pas validé cliniquement** : `clinical_review_status` vaut `not_performed` sur 480/480 lignes. Son texte de justification générique indique encore `project review pending`, tandis que le statut projet indique `approved_for_educational_dpo`. Cette incohérence doit être corrigée par une nouvelle décision tracée, et non par une simple substitution de chaîne. Le manifeste historique ne renseigne pas non plus explicitement `sft_manifest_sha256` malgré la protection par empreintes documentée. Le lot est donc une entrée de revue, pas le jeu DPO clinique final demandé.

La [checklist de revue clinique](../governance/CHECKLIST_REVUE_CLINIQUE_V1.md) précise la décision et les preuves à enregistrer pour chaque paire.

## Métadonnées cliniques

Le schéma [clinical_metadata_v1.schema.json](../../data/manifests/clinical_metadata_v1.schema.json) définit : symptômes, durée, évolution, intensité, antécédents, constantes, vulnérabilités, source immuable, niveau de confiance et statuts d’anonymisation/revue. L’absence est une valeur explicite : `metadata_status: not_available` impose listes vides, constantes nulles et confiance indisponible. Cela évite d’extraire ou d’inventer des informations que les corpus QA ne fournissent pas.

Les exemples [synthetic-clinical-metadata-v1.json](../../data/samples/synthetic-clinical-metadata-v1.json) sont synthétiques. Le candidat SFT v2.1 n’est pas réécrit rétroactivement avec des métadonnées inférées ; une future extraction devra produire une nouvelle version et rester `extracted_pending_review` jusqu’à revue.

## Jeux séparés

- SFT : 3 721 train, 479 validation, 500 test isolé dans le canonique.
- DPO : 426 train, 54 validation ; aucun test UltraMedical n’est copié dans le lot.
- Évaluation de triage : scénarios synthétiques séparés sous `data/samples/`. Leurs références restent `proposed`, et le jeu final déjà consulté ne redevient pas un test aveugle.

## Conditions de passage

Avant de déclarer l’étape complète :

1. terminer la revue contextuelle PII et consigner la décision ligne par ligne ;
2. obtenir la validation clinique du jeu DPO, avec identité/rôle du réviseur, date, protocole et justification ;
3. produire un jeu d’évaluation clinique séparé validé, sans réutiliser le test déjà consulté ;
4. publier ou transmettre les données uniquement par un canal autorisé et compatible avec les licences ;
5. figer un manifeste final reliant explicitement SFT, DPO, schéma, audits et révision Git.

## Reproduction minimale

```bash
PYTHONPATH=src /path/to/project-python scripts/audit_sft_v2_readiness.py \
  --manifest data/manifests/derived-source-medical-qa-sft-v2.1-reviewed.json \
  --artifacts data/processed/source-sft-v2.1-reviewed \
  --original-tokenizer artifacts/sft-v2-pilot-ready/tokenizer \
  --medquad /controlled/path/medquad \
  --mediqal /controlled/path/mediqal \
  --french /controlled/path/frenchmedmcqa-rebuilt \
  --output /fresh/audit/directory --scan-direct-identifiers

PYTHONPATH=src /path/to/project-python -m pytest \
  tests/test_clinical_metadata_schema.py tests/test_source_sft.py -q
```

Ces commandes prouvent les contrats et transformations techniques dans l’environnement testé. Elles ne prouvent ni conformité RGPD globale, ni exactitude médicale, ni validation clinique.
