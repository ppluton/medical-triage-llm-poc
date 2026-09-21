# ADR-022 — Publier le dataset et les adaptateurs sur Hugging Face

- Date : 2026-09-21
- Statut : `approved`
- Propriétaire : Pierre
- Statut clinique : non applicable ; aucune validation clinique
- Sources : [cadrage](../../CADRAGE_MISSION.md), [processus RGPD](../governance/PROCESSUS_RGPD_CORPUS_V1.md),
  [registre des sources](../governance/REGISTRE_SOURCES_DONNEES.md)

## Contexte

La remise demande un dataset versionné sur un dépôt (format Hugging Face ou JSONL) et des poids
finaux chargeables. Le corpus v2.2 et les adaptateurs n'existaient que dans des datasets Kaggle
privés ; la publication externe restait bloquée en attente d'une revue humaine et juridique.

## Décision

Publier en accès public, à des fins pédagogiques :

- [`Pedro1321/chsa-triage-medical-qa-fr-en`](https://huggingface.co/datasets/Pedro1321/chsa-triage-medical-qa-fr-en) :
  configs `sft` (3 721 / 479 / 500, découpage du fichier canonique v2.2) et `dpo` (426 / 54, lot v3) ;
- [`Pedro1321/chsa-triage-qwen3-1.7b-lora`](https://huggingface.co/Pedro1321/chsa-triage-qwen3-1.7b-lora) :
  adaptateurs `sft-v39` (déployé) et `dpo-v41`, poids identiques aux manifestes
  (`c911f9c6…`, `ae66169e…`). Seul `base_model_name_or_path` de `adapter_config.json` pointe
  désormais vers `unsloth/Qwen3-1.7B-Base` à la révision `e249956c…` au lieu du chemin Kaggle.

Justification : toutes les lignes proviennent de sources déjà publiques sous licences ouvertes
(CC BY 4.0, Apache-2.0, MIT) qui autorisent la redistribution d'un dérivé avec attribution ; aucune
donnée hospitalière ni donnée patient réelle n'est incluse ; les identifiants directs détectés
sont remplacés et le rescan ne retrouve aucun identifiant direct. Chaque ligne conserve sa source,
sa licence et ses transformations.

## Conséquences et limites

- La publication ne vaut pas certification d'anonymisation RGPD : 3 199 lignes SFT gardent des
  candidats contextuels (auteurs, éponymes, lieux, durées) déjà présents dans les sources publiques.
- Les fiches Hugging Face rappellent l'usage pédagogique, l'absence de labels de triage, l'absence
  de validation clinique et le résultat négatif du modèle seul.
- Un retrait reste possible en supprimant ou en rendant privés les deux dépôts ; les copies déjà
  téléchargées ne peuvent pas être rappelées.
- Les journaux d'audit, sorties générées et fichiers de revue privés restent hors publication.
