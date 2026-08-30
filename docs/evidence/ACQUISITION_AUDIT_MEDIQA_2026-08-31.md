# Acquisition et audit candidat MEDIQA 2019

- **Date :** 2026-08-31
- **Statut :** partially proven — source candidate, non admise au SFT
- **Sources :** dépôt `abachaa/MEDIQA2019`, révision `32311a139b583a9ccec133b3f8a21873d4ff3561`, `data/manifests/src-mediqa2019-32311a1.json`

## Périmètre

Vérifier la provenance, la licence, les fichiers distribués, les volumes, les labels, les doublons textuels et un échantillon PII de MEDIQA 2019 sans versionner les données brutes.

## Acquisition

- Dépôt tiers utilisé en lecture seule : `https://github.com/abachaa/MEDIQA2019`.
- Commit épinglé : `32311a139b583a9ccec133b3f8a21873d4ff3561`.
- Licence distribuée : CC BY 4.0 avec attribution.
- Archive Git reproductible : 14 735 360 octets, SHA-256 `4a2690a6bb973e32c016c2039e18f4c0831588959adae31d6a9d510320110b18`.
- Checkout brut : `data/raw/mediqa2019/`, ignoré par Git.
- Tâche 1 MedNLI : non acquise ; le dépôt renvoie vers PhysioNet et ses conditions d'accès.

## Inventaire observé

La politique canonique retient les exports de test labellisés et ne recompte pas leurs copies non labellisées.

| Tâche | Train | Validation | Test | Total canonique |
|---|---:|---:|---:|---:|
| RQE — paires | 8 588 | 302 | 230 | 9 120 |
| QA — questions | 208 | 25 | 150 | 383 |
| QA — réponses | 1 701 | 234 | 1 107 | 3 042 |

- Labels RQE : 4 899 `true`, 4 221 `false`.
- Scores QA : 616 scores 1, 1 126 scores 2, 655 scores 3 et 645 scores 4.
- Doublons normalisés : 4 264 instances de questions consommateur RQE, 31 paires RQE complètes et 5 questions QA.
- XML malformés : 0.
- Motifs sur les textes canoniques : 65 placeholders explicites, 6 emails et 149 téléphones. Ces motifs couvrent aussi les réponses documentaires et ne prouvent pas une PII patient.

## Sample Presidio observé

- Versions : Presidio Analyzer/Anonymizer `2.2.364`, spaCy `3.8.16`, `en_core_web_sm 3.8.0`.
- Sélection : 70 questions, dix pour chacun des sept fichiers canoniques.
- Hash de sélection : `b805a97316eca0812ca10d5fae580bc1518e9b229f6e018d485955eb050ef5ed`.
- Statuts : 70 `passed`, aucune entité résiduelle.
- Détections avant remplacement : 27 `DATE_TIME`, 4 `LOCATION`, 12 `PERSON`.
- Les réponses QA sont exclues de ce sample ; aucun texte ni aucune valeur détectée n'est persisté.

## Ce que cela prouve et ne prouve pas

**Prouvé :** la révision, la licence distribuée, le checksum d'archive, les volumes XML, la distribution des labels, les doublons normalisés et le comportement du sample Presidio sont reproductibles localement.

**Non prouvé :** l'absence de PII dans le corpus complet, l'absence de fuite sémantique, l'adéquation clinique, la conformité juridique définitive et la possibilité de transformer les labels existants en niveaux de triage. MEDIQA reste `candidate`.
