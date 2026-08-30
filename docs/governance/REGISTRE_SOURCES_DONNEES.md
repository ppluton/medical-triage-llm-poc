# Registre de gouvernance des sources de données

- **Date :** 2026-08-31
- **Statut :** draft — FrenchMedMCQA, MedQuAD et MEDIQA acquis et audités comme candidats ; aucune source externe approuvée pour l'entraînement
- **Périmètre :** sources citées par `SPEC_POC_TRIAGE_MEDICAL.md`
- **Propriétaire :** projet d'étude POC Agent IA de triage médical

## Objet

Ce registre permet de décider si une source peut entrer dans le pipeline. Une licence affichée ne constitue pas, à elle seule, l'autorisation de l'utiliser pour le POC : l'acceptation dépend aussi de la provenance, de la compatibilité avec l'objectif de triage, du risque de données sensibles, de la transformation envisagée et de l'isolement de l'évaluation.

## État de décision

| Source | Usage envisagé | Licence affichée à la source | Statut actuel | Décision avant ingestion |
|---|---|---|---|---|
| MEDIQA 2019 | Évaluation QA/RQE, pas de référentiel de triage | CC BY 4.0 | candidate auditée | Révision `32311a1…` épinglée ; tâches 2–3 seulement ; revue PII et déduplication requises |
| FrenchMedMCQA | Couverture française, baseline MCQA | Apache-2.0 | candidate sous contrôle | Respecter les splits natifs ; ne pas transformer automatiquement les QCM en recommandations de triage |
| MedQuAD | Questions-réponses médicales générales | CC BY 4.0 | candidate auditée | Révision `577bd37…` épinglée ; exclure les sous-ensembles 10–12 ; revue PII et clinique requise avant toute sélection |
| UltraMedical-Preference | Paires de préférences pour DPO | MIT | candidate sous contrôle | Contrôler le schéma, la révision, la qualité et l'adéquation au triage avant toute sélection |

**Aucune source n'est encore approuvée pour l'entraînement.** La décision sera prise par sous-ensemble et par transformation, pas globalement par nom de dataset.

## Fiches de provenance

### MEDIQA 2019

- **Référence primaire :** [dépôt `abachaa/MEDIQA2019`](https://github.com/abachaa/MEDIQA2019)
- **Version acquise :** commit `32311a139b583a9ccec133b3f8a21873d4ff3561`, archive et checksum consignés dans `data/manifests/src-mediqa2019-32311a1.json`.
- **Contenu observé :** tâches 2 RQE et 3 QA ; 9 120 paires RQE, 383 questions QA et 3 042 réponses dans les exports canoniques.
- **Licence affichée :** Creative Commons Attribution 4.0 International (CC BY 4.0).
- **Usage POC envisagé :** évaluation ou transformation limitée vers des tâches de compréhension médicale, jamais comme validation clinique de triage.
- **Risques / contrôles :** tâche 1 MedNLI exclue car non distribuée dans le dépôt et contrôlée via PhysioNet ; labels RQE/QA interdits comme cibles automatiques de triage ; préserver citation et attribution.
- **PII :** sample déterministe de 70 questions passé sans résidu, mais le corpus complet et les réponses nécessitent encore un contrôle et une revue humaine.

### FrenchMedMCQA

- **Référence primaire :** [dataset `qanastek/frenchmedmcqa`](https://huggingface.co/datasets/qanastek/frenchmedmcqa)
- **Version à épingler avant téléchargement :** révision Hugging Face (commit SHA), à renseigner dans le manifeste.
- **Contenu :** 3 105 questions de QCM médical en français, issues d'examens français de spécialisation en pharmacie ; cinq propositions et une ou plusieurs réponses correctes.
- **Licence affichée :** Apache License 2.0.
- **Déclaration de données sensibles :** la dataset card indique l'absence d'informations personnelles ou sensibles.
- **Usage POC envisagé :** baseline de compréhension médicale francophone et évaluation de format QCM ; ce corpus ne contient pas, à lui seul, une politique de triage.
- **Risques / contrôles :** préserver les splits natifs ; ne pas convertir mécaniquement une bonne réponse d'examen en conseil médical ni en niveau de priorité ; soumettre toute transformation SFT à une revue clinique.

### MedQuAD

- **Référence primaire :** [dépôt `abachaa/MedQuAD`](https://github.com/abachaa/MedQuAD)
- **Version à épingler avant téléchargement :** commit Git précis et checksum de l'archive, à renseigner dans le manifeste.
- **Contenu :** 47 457 paires question-réponse provenant de 12 sites NIH, avec annotations complémentaires dans les fichiers XML.
- **Licence affichée :** Creative Commons Attribution 4.0 International (CC BY 4.0).
- **Restriction documentée :** le dépôt a retiré les réponses de trois sous-ensembles pour respecter le droit d'auteur de MedlinePlus (A.D.A.M. Medical Encyclopedia, médicaments et compléments).
- **Usage POC envisagé :** questions-réponses générales ; sélection contrôlée, sans recrawl de sources externes ni reconstitution des réponses retirées.
- **Risques / contrôles :** vérifier le contenu exact distribué, attribuer la source, évaluer la pertinence pour le triage et appliquer les contrôles PII même si la provenance est institutionnelle.

### UltraMedical-Preference

- **Référence primaire :** [dataset `TsinghuaC3I/UltraMedical-Preference`](https://huggingface.co/datasets/TsinghuaC3I/UltraMedical-Preference) ; [dépôt de publication UltraMedical](https://github.com/TsinghuaC3I/UltraMedical)
- **Version à épingler avant téléchargement :** révision Hugging Face (commit SHA) et checksums des fichiers réellement retenus.
- **Contenu :** données de préférences biomédicales en anglais ; la publication annonce plus de 100 000 données de préférence dans la collection UltraMedical.
- **Licence affichée :** MIT.
- **Usage POC envisagé :** candidat pour le DPO, après filtrage par type, langue et sécurité.
- **Risques / contrôles :** le visualiseur Hugging Face signalait, lors de la consultation du 2026-08-28, un schéma de colonnes incohérent entre fichiers. Inspecter les fichiers et normaliser explicitement le schéma avant ingestion ; ne pas supposer que toutes les paires sont adaptées au triage ; vérifier la provenance des composants synthétiques et documenter les exclusions.

## Critères d'acceptation avant ingestion

Une source ou un sous-ensemble ne passe de `candidate sous contrôle` à `approved` que si tous les critères suivants sont prouvés dans `data/manifests/` et `docs/evidence/` :

1. URL primaire, version immuable, licence et citation enregistrées.
2. Fichiers exacts, volume, checksum et date de récupération documentés.
3. Objectif d'usage, transformations et exclusions justifiés.
4. Détection PII exécutée, revue d'échantillons documentée et décision de traitement enregistrée.
5. Split d'origine préservé ou nouveau split justifié, sans fuite vers l'évaluation isolée.
6. Contrôle de format, de langue, de doublons et de contenu dangereux exécuté.
7. Validation de l'adéquation clinique demandée lorsque le contenu est utilisé pour produire une priorité, une recommandation ou une règle d'escalade.

## État d’acquisition au 2026-08-31

FrenchMedMCQA, MedQuAD et MEDIQA 2019 ont été acquis localement dans `data/raw/`, hors Git. MedQuAD a fait l’objet d’un inventaire complet et d’un sample Presidio de 90 paires. MEDIQA a fait l’objet d’un inventaire complet de ses tâches 2–3 et d’un sample Presidio de 70 questions. Leurs manifestes restent `candidate`. UltraMedical-Preference n'est pas encore acquis localement ; sa révision et ses volumes distants ont été identifiés avant téléchargement.

## Ce que ce document prouve et ne prouve pas

Il prouve qu'une lecture des pages de référence et des audits locaux a établi les licences affichées, rôles possibles et précautions des sources acquises. Il ne prouve ni la conformité juridique définitive, ni l'absence de PII dans les corpus complets, ni la qualité clinique, ni l'aptitude d'une donnée à entraîner un agent de triage.

## Sources consultées

- [MEDIQA2019 — dépôt et licence](https://github.com/abachaa/MEDIQA2019)
- [FrenchMedMCQA — dataset card](https://huggingface.co/datasets/qanastek/frenchmedmcqa)
- [MedQuAD — dépôt et restriction sur trois sous-ensembles](https://github.com/abachaa/MedQuAD)
- [UltraMedical-Preference — dataset card et révision](https://huggingface.co/datasets/TsinghuaC3I/UltraMedical-Preference)
- [UltraMedical — dépôt de publication et description de la collection](https://github.com/TsinghuaC3I/UltraMedical)
