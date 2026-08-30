# Acquisition et audit candidat MedQuAD

- **Date :** 2026-08-31
- **Statut :** partially proven — source candidate, non admise au SFT
- **Sources :** dépôt `abachaa/MedQuAD`, révision `577bd37b96c02d1833b2c9eed2de9f96964e96cb`, `data/manifests/src-medquad-577bd37.json`

## Périmètre

Vérifier la provenance, la licence, la structure distribuée, les réponses disponibles, les doublons textuels et un échantillon PII de MedQuAD sans publier les données brutes.

## Acquisition

- Dépôt tiers utilisé en lecture seule : `https://github.com/abachaa/MedQuAD`.
- Commit épinglé : `577bd37b96c02d1833b2c9eed2de9f96964e96cb`.
- Licence distribuée : CC BY 4.0 avec attribution.
- Archive Git reproductible : 45 649 920 octets, SHA-256 `9dd2db77967323da64d1514e0125b44fcce2e59ab5b2da16eba99245649c64a8`.
- Checkout brut : `data/raw/medquad/`, ignoré par Git.

## Inventaire observé

- Fichiers XML : 11 274 ; XML malformés : 0.
- Paires QA : 47 441.
- Réponses non vides : 16 407 ; réponses vides : 31 034.
- Instances de questions dupliquées après normalisation : 1 444.
- Motifs regex : 13 emails et 150 téléphones ; ces comptes exigent une revue et ne prouvent pas la présence de PII patient.
- Sous-ensembles 10, 11 et 12 : 31 029 réponses vides et exclusion obligatoire conformément au README amont.

Le rapport agrégé hors Git est `artifacts/medquad-candidate-audit-2026-08-31.json`, SHA-256 `2764b495162e06b7c9c0ecba2bb1eae41db789938a25677d2581f0fb711457b4`.

## Sample Presidio observé

- Versions : Presidio Analyzer/Anonymizer `2.2.364`, spaCy `3.8.16`, `en_core_web_sm 3.8.0`.
- Sélection : 90 paires, dix par chacun des neuf sous-ensembles avec réponses.
- Statuts : 89 `passed`, 1 `manual_review_required` à cause d’une détection résiduelle `PERSON`.
- Détections avant remplacement : 97 `PERSON`, 95 `LOCATION`, 93 `DATE_TIME`.
- Aucun texte ni valeur détectée n’a été persisté.
- Rapport hors Git : SHA-256 `8d20b56cd59f6980522093214eb03de1f5b5f16ff96c09cff3d29369f34fc30f`.

## Ce que cela prouve et ne prouve pas

**Prouvé :** la révision, la licence distribuée, l’inventaire XML, les réponses retirées, les volumes et le comportement du sample Presidio sont reproductibles localement.

**Non prouvé :** l’absence de PII sur le corpus complet, la pertinence clinique, la conformité juridique définitive et l’adéquation directe au SFT de triage. La source reste `candidate`.

## File de rédaction observée

Une sélection équilibrée de 200 paires `symptoms` a été soumise à l’anonymiseur réel. 193 entrées ont été conservées et 7 rejetées pour PII résiduelle. La file locale `data/processed/medquad-review-queue-v1.json` pèse 491 679 octets et porte le SHA-256 `574d2ec5829a9982f509e26c67dd29831fe5c0c447bbbac1c0ce8f6a82938ece`.

La file contient 34 sources CancerGov, 34 GARD, 36 NIDDK, 36 SeniorHealth, 35 NHLBI et 18 CDC. Ces entrées restent des aides documentaires sans cible de triage ; elles ne sont pas des données SFT.
