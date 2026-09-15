# Contrat de données v1 — exemples SFT, DPO et manifestes de source

- **Date :** 2026-08-28
- **Statut :** proposed
- **Sources :** `SPEC_POC_TRIAGE_MEDICAL.md`, `docs/governance/REGISTRE_SOURCES_DONNEES.md`, `docs/decisions/ADR-001-ingestion-conditionnelle-des-sources.md`
- **Artefacts normatifs :** `data/manifests/triage_record_v1.schema.json` et `data/manifests/source_manifest_v1.schema.json`
- **Complément de reprise :** `data/manifests/clinical_metadata_v1.schema.json` décrit les métadonnées cliniques d'un corpus QA lorsque les cibles de triage de `triage_record_v1` ne s'appliquent pas.

## Objectif

Ce contrat décrit les métadonnées minimales permettant de tracer un exemple transformé et un fichier source sans versionner le dataset brut. Il couvre les exemples SFT, les paires DPO et les évaluations ; il ne définit pas une règle clinique de triage ni un seuil d'acceptation.

## Deux niveaux de traçabilité

| Niveau | Artefact | Question à laquelle il répond |
|---|---|---|
| Fichier de source | `source_manifest_v1.schema.json` | Quel fichier exact a été obtenu, d'où, sous quelle licence, version et checksum ? |
| Enregistrement transformé | `triage_record_v1.schema.json` | Quel exemple a été produit, à partir de quelle source, avec quelle transformation, anonymisation et split ? |

Un enregistrement transformé référence un `source_manifest_id`. Un manifeste ne contient pas les exemples sources ou un texte clinique : il contient seulement des métadonnées et des empreintes.

## Contrat commun d'un enregistrement transformé

Chaque enregistrement contient obligatoirement :

- `schema_version` : `1.0.0` ;
- `record_id` : identifiant stable préfixé par `sft-`, `dpo-` ou `eval-` ;
- `task_type` : `sft`, `dpo` ou `evaluation` ;
- `language` : `fr` ou `en` ;
- `source` : identifiant d'exemple source, manifeste, URL et licence ;
- `transformation` : version, hash Git, nom du pipeline et identifiant du run ;
- `quality` : résultat PII, statut de revue et niveau de sécurité ;
- `split` : `train`, `validation` ou `test`.

Les champs de contenu comprennent un contexte patient minimalisé (`age_group`, symptômes, durée, antécédents catégorisés, constantes optionnelles et vulnérabilités). L'âge exact, les dates, les noms, les coordonnées, les identifiants hospitaliers et le texte libre non anonymisé sont interdits.

## Cas SFT

Un enregistrement `sft` ajoute `sft_target`, qui respecte le contrat de sortie de l'API : niveau de priorité, synthèse, raisonnement clinique, informations manquantes, signaux d'alerte, recommandation encadrée et avertissement de sécurité.

La présence d'un niveau `maximum`, `moderate` ou `deferred` est une structure technique imposée par la spécification. Elle ne signifie pas que la cible a été approuvée cliniquement : seul `quality.clinical_review_status: "approved"` peut l'indiquer.

## Cas DPO

Un enregistrement `dpo` ajoute une paire `dpo_pair` : un même prompt et deux réponses structurées, `chosen` et `rejected`, ainsi qu'une justification de préférence. Les paires sont destinées à l'alignement ; elles n'entrent pas automatiquement dans le SFT ni dans l'évaluation.

Le champ `preference_review_status` doit rester à `pending` tant qu'une revue appropriée n'a pas été documentée. Les préférences fondées sur un score automatique doivent être identifiées comme telles dans le journal de transformation ; elles ne valent pas revue clinique.

## Cas d'évaluation

Un enregistrement `evaluation` peut contenir un objectif attendu (`expected_triage_level`) ou aucun objectif lorsque le scénario sert à tester la robustesse, l'information insuffisante ou les garde-fous. Le jeu `test` est isolé : aucune correction de modèle, prompt ou hyperparamètre ne peut être choisie à partir de ses résultats.

## Contrat du manifeste de source

Avant tout téléchargement, un manifeste par fichier source est créé avec :

- `manifest_id`, nom du dataset et URL primaire ;
- révision immuable (SHA Git ou révision Hugging Face) ;
- chemin du fichier, date de récupération, taille et SHA-256 ;
- licence et citation ;
- statut d'admissibilité et restrictions ;
- résultats des contrôles pré-ingestion ;
- chemins de sortie prévus, sans fichier brut dans Git.

`approved` n'est autorisé que si tous les contrôles de provenance, PII, licence, split et qualité de format sont à `passed`. Les fichiers qui échouent restent traçables avec le statut `rejected` ou `quarantined`.

## Cycle de vie

```text
candidate source
  → manifeste créé et révision épinglée
  → téléchargement hors Git + checksum
  → contrôles licence / PII / format / doublons
  → approved, rejected ou quarantined
  → transformation versionnée vers SFT, DPO ou evaluation
  → validation du schéma de l'enregistrement
  → preuve de split et de revue
```

## Ce que ce contrat prouve et ne prouve pas

Il prouve une structure prévue pour la traçabilité et les contrôles. Il ne prouve pas que le pipeline existe déjà, que les données passent les contrôles, que les cibles sont cliniquement validées ou que le modèle est performant. Ces preuves seront produites dans `docs/evidence/` lorsque les scripts et jeux de données existeront.
