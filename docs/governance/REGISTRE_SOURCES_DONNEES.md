# Registre de gouvernance des sources de données

- **Date :** 2026-09-03
- **Statut :** draft — source MediQAl corrigée et file v2 générée ; aucune source externe approuvée pour l'entraînement
- **Périmètre :** sources citées par `SPEC_POC_TRIAGE_MEDICAL.md`
- **Propriétaire :** projet d'étude POC Agent IA de triage médical

## Objet

Ce registre permet de décider si une source peut entrer dans le pipeline. Une licence affichée ne constitue pas, à elle seule, l'autorisation de l'utiliser pour le POC : l'acceptation dépend aussi de la provenance, de la compatibilité avec l'objectif de triage, du risque de données sensibles, de la transformation envisagée et de l'isolement de l'évaluation.

## État de décision

| Source | Usage envisagé | Licence affichée à la source | Statut actuel | Décision avant ingestion |
|---|---|---|---|---|
| MediQAl | QCM médicaux francophones comme ancrages documentaires | CC BY 4.0 | candidate auditée, fuite de split mesurée | Révision `5af3494…` épinglée ; test et recouvrements avec test exclus ; revue PII et clinique requise |
| FrenchMedMCQA | Couverture française, baseline MCQA | Apache-2.0 | candidate sous contrôle | Respecter les splits natifs ; ne pas transformer automatiquement les QCM en recommandations de triage |
| MedQuAD | Questions-réponses médicales générales | CC BY 4.0 | candidate auditée | Révision `577bd37…` épinglée ; exclure les sous-ensembles 10–12 ; revue PII et clinique requise avant toute sélection |
| UltraMedical-Preference | Paires de préférences pour DPO | MIT | candidate auditée, fuite de split | Révision `761eb79…` épinglée ; reconstruire les splits ; réserver le test à l'évaluation |

**Aucune source n'est encore approuvée pour l'entraînement.** La décision sera prise par sous-ensemble et par transformation, pas globalement par nom de dataset.

## Fiches de provenance

### MediQAl

- **Référence primaire :** [dataset `ANR-MALADES/MediQAl`](https://huggingface.co/datasets/ANR-MALADES/MediQAl)
- **Version acquise :** commit `5af34948a74c7b8807c476204a21149ffb00ea2c`, fichiers et checksum de collection consignés dans `data/manifests/src-mediqal-5af3494.json`.
- **Contenu observé :** 32 603 questions d'examens médicaux français : 17 017 MCQU, 10 617 MCQM et 4 969 OEQ.
- **Licence affichée :** Creative Commons Attribution 4.0 International (CC BY 4.0).
- **Usage POC envisagé :** ancrages documentaires francophones pour la rédaction de scénarios synthétiques, jamais comme validation clinique de triage.
- **Risques / contrôles :** 399 recouvrements normalisés `train/test`, 478 `train/validation` et 112 `validation/test` ; tous les tests et leurs recouvrements sont exclus de la file.
- **PII :** Presidio a rejeté 56 ancrages résiduels pendant la génération v2 ; cela ne prouve pas l'absence de PII dans le corpus complet.

### Historique MEDIQA 2019

`abachaa/MEDIQA2019` a été acquis et audité avant la clarification de la source. Son manifeste et ses preuves restent versionnés comme historique, mais ce corpus n'entre plus dans la file courante depuis ADR-006.

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
- **Version acquise :** révision `761eb7935310ba662a96d93c5af342e5269d5759`, fichiers et checksums consignés dans `data/manifests/src-ultramedical-preference-761eb79.json`.
- **Contenu observé :** 109 353 paires `train`, 2 232 `dev` et 777 `test`, au format prompt/conversations choisie et rejetée/métadonnées.
- **Licence affichée :** MIT.
- **Usage POC envisagé :** candidat pour le DPO, après filtrage par type, langue et sécurité.
- **Risques / contrôles :** schéma local cohérent, mais 1 228 chevauchements `train/dev`, 30 `train/test` et 1 `dev/test` ; reconstruction obligatoire. Un sample Presidio de 30 triples conserve une détection `PERSON` résiduelle. Ne pas supposer que toutes les paires sont adaptées au triage.

## Critères d'acceptation avant ingestion

Une source ou un sous-ensemble ne passe de `candidate sous contrôle` à `approved` que si tous les critères suivants sont prouvés dans `data/manifests/` et `docs/evidence/` :

1. URL primaire, version immuable, licence et citation enregistrées.
2. Fichiers exacts, volume, checksum et date de récupération documentés.
3. Objectif d'usage, transformations et exclusions justifiés.
4. Détection PII exécutée, revue d'échantillons documentée et décision de traitement enregistrée.
5. Split d'origine préservé ou nouveau split justifié, sans fuite vers l'évaluation isolée.
6. Contrôle de format, de langue, de doublons et de contenu dangereux exécuté.
7. Validation de l'adéquation clinique demandée lorsque le contenu est utilisé pour produire une priorité, une recommandation ou une règle d'escalade.

## État d’acquisition au 2026-09-03

MediQAl, FrenchMedMCQA, MedQuAD et UltraMedical-Preference ont été acquis localement dans `data/raw/`, hors Git, à des révisions épinglées. Les quatre manifestes restent `candidate`. Les miroirs `nthngdy/frenchmedmcqa` et `keivalya/MedQuad-MedicalQnADataset` transmis comme références secondaires ne remplacent pas les sources canoniques déjà auditées : leurs dataset cards n'affichent pas de licence et leurs périmètres diffèrent des corpus canoniques.

## Ce que ce document prouve et ne prouve pas

Il prouve qu'une lecture des pages de référence et des audits locaux a établi les licences affichées, rôles possibles et précautions des sources acquises. Il ne prouve ni la conformité juridique définitive, ni l'absence de PII dans les corpus complets, ni la qualité clinique, ni l'aptitude d'une donnée à entraîner un agent de triage.

## Sources consultées

- [MediQAl — dataset card, licence et splits](https://huggingface.co/datasets/ANR-MALADES/MediQAl)
- [FrenchMedMCQA — dataset card](https://huggingface.co/datasets/qanastek/frenchmedmcqa)
- [MedQuAD — dépôt et restriction sur trois sous-ensembles](https://github.com/abachaa/MedQuAD)
- [UltraMedical-Preference — dataset card et révision](https://huggingface.co/datasets/TsinghuaC3I/UltraMedical-Preference)
- [UltraMedical — dépôt de publication et description de la collection](https://github.com/TsinghuaC3I/UltraMedical)
