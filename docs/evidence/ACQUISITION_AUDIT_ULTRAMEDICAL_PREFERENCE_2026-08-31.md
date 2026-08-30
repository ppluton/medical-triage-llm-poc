# Acquisition et audit candidat UltraMedical-Preference

- **Date :** 2026-08-31
- **Statut :** partially proven — source candidate, splits amont non admissibles tels quels
- **Sources :** dataset `TsinghuaC3I/UltraMedical-Preference`, révision `761eb7935310ba662a96d93c5af342e5269d5759`, `data/manifests/src-ultramedical-preference-761eb79.json`

## Périmètre

Vérifier la provenance, la licence, le schéma DPO, les volumes, les doublons, les chevauchements de split et un échantillon PII avant toute préparation d'entraînement.

## Acquisition

- Révision Hugging Face épinglée : `761eb7935310ba662a96d93c5af342e5269d5759`.
- Licence affichée dans la dataset card : MIT.
- Fichiers conservés hors Git : `train.json`, `dev.json`, `test.json` et `README.md`.
- Volume cumulé des trois splits : 1 019 500 856 octets.
- SHA-256 de la concaténation ordonnée `train`, `dev`, `test` : `d40f19d8feb6f56e2310207e065716eb791449e2acd215b5705726869cdc926c`.
- SHA-256 individuels : `train` `c3e4a3b078c425ada0750917d846fcdac835520de6e1755ae9a137fc7ca172e0`, `dev` `4f6b0a1350f2664caeefd2d628eae992ba732d475138fcdbe2657a25f70f9269`, `test` `38f21a20407a401d55c1a0939f436ac1c2d5216bec31c126a55d7ed0f2c9d251`.

## Inventaire observé

| Split | Lignes | Doublons `prompt_id` | Doublons de prompt normalisé | Usage autorisé à ce stade |
|---|---:|---:|---:|---|
| train | 109 353 | 32 307 | 33 152 | candidat entraînement après reconstruction |
| dev | 2 232 | 17 | 17 | candidat validation après reconstruction |
| test | 777 | 1 | 1 | évaluation uniquement |

Toutes les lignes ont les clés requises, des conversations `user/assistant`, des réponses choisies et rejetées distinctes et des métadonnées structurées. Aucun défaut de structure n'a été observé.

### Chevauchements normalisés

- `train` / `dev` : 1 228 prompts.
- `train` / `test` : 30 prompts.
- `dev` / `test` : 1 prompt.

Le contrôle `split_leakage` du manifeste est donc `failed`. Une reconstruction déterministe est obligatoire avant toute expérience.

### Composition

Le split d'entraînement regroupe notamment MedQA, MedMCQA, MedQA-Evol, TextBookQA, PubMedQA, ChatDoctor, MedQuad, MedInstruct-52k, Medical-Instruct-120k et WikiInstruct. Les labels de préférence sont `easy`, `hard` et `length`. Le test ajoute 163 paires `human` et constitue le Medical RewardBench décrit par la dataset card.

## Sample Presidio observé

- Sélection : 30 triples complets, dix par split, incluant prompt, réponse choisie et réponse rejetée.
- Hash de sélection : `1bf1c2074528358b7e3a199fa187cb5f75789d8db7c912138f8f32d0fe970091`.
- Statuts : 29 `passed`, 1 `manual_review_required` pour une entité résiduelle `PERSON`.
- Détections initiales : 148 `DATE_TIME`, 32 `LOCATION`, 137 `PERSON`.
- Aucun texte ni valeur détectée n'est persisté.

## Ce que cela prouve et ne prouve pas

**Prouvé :** la révision, les fichiers, les checksums, le volume, le schéma, les distributions, les doublons, les chevauchements normalisés et le comportement du sample Presidio sont reproductibles localement.

**Non prouvé :** l'absence de PII sur le corpus complet, l'absence de paraphrases entre splits, la qualité factuelle de chaque préférence, son adéquation au triage et la sûreté clinique. La source reste `candidate` et ne peut pas encore entrer dans le DPO.
