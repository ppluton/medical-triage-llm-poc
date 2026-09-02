# Génération de la file SFT candidate v2 avec MediQAl

- **Date :** 2026-09-03
- **Statut :** proven pour la génération technique ; not proven pour le SFT et la validation clinique
- **Code :** `29c9af0`
- **Run :** `sft-authoring-queue-v2-2026-09-03`
- **Sources :** manifeste `src-mediqal-5af3494`, manifeste dérivé `derived-sft-authoring-queue-v2`

## Claim vérifié

Le pipeline corrigé peut générer exactement 5 000 candidats bilingues traçables à partir de MedQuAD, MediQAl et FrenchMedMCQA, sans inclure de cible de triage ni rendre une ligne entraînable.

## Environnement et commande

Exécution locale macOS avec Python 3.13, Presidio, `fr_core_news_md` et `en_core_web_sm`. La commande complète est consignée dans `docs/technical/FILE_REDACTION_SFT_5000_V2.md`.

Un premier run a échoué avant écriture parce que le schéma candidat impose `transformation.pipeline_version: 1.0.0`. Le code a été corrigé pour conserver ce contrat, puis le run a été repris intégralement.

## Résultats observés

- 5 000 enregistrements, 2 500 groupes bilingues ;
- 2 500 tâches françaises et 2 500 anglaises ;
- MedQuAD 2 000, MediQAl 1 500, FrenchMedMCQA 1 500 ;
- 0 ligne entraînable, 0 cible de triage, 0 split final ;
- 50 lots de revue de 100 lignes ;
- 98 rejets pour PII résiduelle lors du recomplètement : 9 MedQuAD, 56 MediQAl, 33 FrenchMedMCQA ;
- 19 doublons exacts ignorés : 11 MedQuAD, 2 MediQAl, 6 FrenchMedMCQA ;
- 26 ancrages MedQuAD tronqués ; aucun ancrage MediQAl ou FrenchMedMCQA tronqué.

## Intégrité

- file : `e4ac60c336aeb24dfb602f8e6f4539217f6f751239ac321946322a9ff68bdd9d` ;
- index sans texte : `21a0e2d19f54ac1f311c6b9896f524326576ea7fff697950cb066150b08ed500` ;
- les 50 checksums de lots, le checksum de la file et celui de l'index ont été recalculés indépendamment et correspondent au manifeste.

## Ce que cela prouve et ne prouve pas

**Prouvé :** sélection déterministe, exclusion lexicale des recouvrements MediQAl avec le test, validation de schéma, volume, distributions, portes non entraînables et intégrité des artefacts.

**Non prouvé :** absence complète de PII, absence de paraphrases entre splits, pertinence clinique, qualité des futurs labels, conformité RGPD juridique, sûreté d'un modèle ou autorisation d'entraîner.
