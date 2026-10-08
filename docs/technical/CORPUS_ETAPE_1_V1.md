# Corpus de l’étape 1 — état reproductible

Date : 2026-09-16 — Statut : publié à des fins pédagogiques sur [Hugging Face](https://huggingface.co/datasets/Pedro1321/chsa-triage-medical-qa-fr-en) ([ADR-022](../decisions/ADR-022-publier-dataset-et-adaptateurs-hugging-face.md))

Sources : [spécification d’exécution](../archive/SPEC_EXECUTION_V1.md), [registre des sources](../governance/REGISTRE_SOURCES_DONNEES.md), [manifeste SFT v2.2](../../data/manifests/derived-source-medical-qa-sft-v2.2-privacy-finalized.json), [preuve datée](../evidence/AUDIT_CORPUS_ETAPE_1_2026-09-16.md), [finalisation PII](../evidence/SFT_PRIVACY_FINALIZATION_2026-09-16.md).

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

`derived-source-medical-qa-sft-v2.2-privacy-finalized` contient **4 700 paires**, soit 3 721 train, 479 validation et 500 test. La répartition est 2 474 français / 2 226 anglais :

| Source | Enregistrements |
|---|---:|
| MediQAl | 1 475 |
| FrenchMedMCQA | 999 |
| MedQuAD | 2 226 |

Le canonique conserve la provenance de chaque ligne, les opérations de transformation, le statut d’anonymisation et le split. Les choix QCM sont rendus avant la réponse, les contenus trop longs sont exclus plutôt que tronqués et le test n’est pas rendu pour l’entraînement. Aucun `triage_label` n’a été inventé : ce corpus apprend de la QA médicale, pas une politique de priorité validée.

Les artefacts textuels restent hors Git public dans `data/processed/source-sft-v2.1-reviewed/`. Leurs SHA-256 et volumes sont consignés dans le manifeste versionné.

Le scan contextuel initial a parcouru les 9 400 champs du canonique. La v2.2 masque les
31 détections `PATIENT_NAME` sur 22 lignes avec des positions et checksums vérifiés. Son
rescan intégral ne contient plus d'identifiant direct : 1 501 lignes sont sans détection et
3 199 conservent seulement `PERSON`, `LOCATION` ou `DATE_TIME` sous la politique des
sources médicales publiques. Ce résultat ouvre l'entraînement local contrôlé, pas la
publication ni une certification RGPD.

## Lot DPO disponible

`artifacts/dpo-reviewed-v2/` contient 426 paires train et 54 validation, toutes en anglais et issues d’UltraMedical-Preference. Les empreintes des deux JSONL correspondent au [manifeste compact versionné](../../data/manifests/derived-ultramedical-dpo-v2-project-reviewed.json). Les lignes conservent le locator, la révision source, le type de préférence et les statuts de revue.

Le lot possède une revue de projet `approved_for_educational_dpo` mais **aucune revue professionnelle n'est revendiquée** : `clinical_review_status` vaut correctement `not_performed` sur 480/480 lignes. Le scénario OpenClassrooms ne fournit pas de clinicien réel ; cette absence n'empêche donc pas l'expérimentation DPO du POC.

La [consolidation DPO v2](../evidence/DPO_PROJECT_REVIEW_V2_2026-09-16.md) supprime la contradiction `project review pending`, relie chaque ligne à `ADR-014` et relie explicitement le manifeste aux 4 700 prompts SFT protégés. Les champs d'apprentissage et de provenance sont identiques à la version utilisée par l'expérience historique ; cette correction de gouvernance n'impose donc aucun réentraînement.

La [checklist de revue clinique](../governance/CHECKLIST_REVUE_CLINIQUE_V1.md) précise la décision et les preuves à enregistrer pour chaque paire.

## Métadonnées cliniques

Le schéma [clinical_metadata_v1.schema.json](../../data/manifests/clinical_metadata_v1.schema.json) définit : symptômes, durée, évolution, intensité, antécédents, constantes, vulnérabilités, source immuable, niveau de confiance et statuts d’anonymisation/revue. L’absence est une valeur explicite : `metadata_status: not_available` impose listes vides, constantes nulles et confiance indisponible. Cela évite d’extraire ou d’inventer des informations que les corpus QA ne fournissent pas.

Les exemples [synthetic-clinical-metadata-v1.json](../../data/samples/synthetic-clinical-metadata-v1.json) sont synthétiques. Le candidat SFT v2.1 n’est pas réécrit rétroactivement avec des métadonnées inférées ; une future extraction devra produire une nouvelle version et rester `extracted_pending_review` jusqu’à revue.

## Jeux séparés

- SFT : 3 721 train, 479 validation, 500 test isolé dans le canonique.
- DPO : 426 train, 54 validation ; aucun test UltraMedical n’est copié dans le lot.
- Évaluation de triage : scénarios synthétiques séparés sous `data/samples/`. Leurs références restent `proposed`, et le jeu final déjà consulté ne redevient pas un test aveugle.

## Conditions de passage

L'étape 1 est complète pour le périmètre scolaire d'entraînement local contrôlé. Les portes
restantes s'appliquent à une diffusion ou à un pilote réel :

1. ne pas publier ni transmettre v2.2 sans revue humaine/juridique et canal autorisé ;
2. utiliser un jeu d'évaluation de POC séparé et ne pas régler le modèle sur le test consulté ;
3. réserver la validation par des professionnels de santé à la roadmap d'un pilote réel ;
4. produire une nouvelle version, de nouveaux hashes et un nouveau rescan après toute
   transformation textuelle.

## Reproduction minimale

```bash
PYTHONPATH=src /path/to/project-python scripts/audit_sft_v2_readiness.py \
  --manifest data/manifests/derived-source-medical-qa-sft-v2.2-privacy-finalized.json \
  --artifacts data/processed/source-sft-v2.2-privacy-finalized \
  --original-tokenizer artifacts/sft-v2-pilot-ready/tokenizer \
  --medquad /controlled/path/medquad \
  --mediqal /controlled/path/mediqal \
  --french /controlled/path/frenchmedmcqa-rebuilt \
  --output /fresh/audit/directory --scan-direct-identifiers

PYTHONPATH=src /path/to/project-python -m pytest \
  tests/test_clinical_metadata_schema.py tests/test_source_sft.py -q

PYTHONPATH=src /path/to/project-python scripts/audit_sft_contextual_pii.py \
  --canonical data/processed/source-sft-v2.2-privacy-finalized/source-sft-v2.2.jsonl \
  --output /fresh/private/audit-directory
```

Ces commandes prouvent les contrats et transformations techniques dans l’environnement testé. Elles ne prouvent ni conformité RGPD globale, ni exactitude médicale, ni validation clinique.
