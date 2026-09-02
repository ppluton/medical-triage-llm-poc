# ADR-006 — Remplacer MEDIQA 2019 par MediQAl

- **Date :** 2026-09-03
- **Statut :** approved for candidate processing only
- **Propriétaire :** équipe POC
- **Statut clinique :** not approved
- **Sources :** consigne du porteur du POC, `ANR-MALADES/MediQAl` révision `5af34948a74c7b8807c476204a21149ffb00ea2c`, manifeste `src-mediqal-5af3494`

## Contexte

Le mandat mentionnait « MediQA » sans identifiant immuable. Une clarification ultérieure désigne explicitement le dataset francophone `ANR-MALADES/MediQAl`. La file v1 utilisait `abachaa/MEDIQA2019`, corpus anglophone différent consacré à l'entailment et au classement de réponses.

MediQAl contient 32 603 questions issues d'examens médicaux français : 17 017 MCQU, 10 617 MCQM et 4 969 OEQ. Son audit local mesure des recouvrements de questions normalisées entre splits, dont 399 `train/test`, 478 `train/validation` et 112 `validation/test`.

## Décision

- Retirer MEDIQA 2019 de la file de rédaction courante sans supprimer ses preuves historiques.
- Utiliser uniquement les configurations MCQU et MCQM de MediQAl pour les ancrages documentaires.
- Exclure tous les exports `test`, l'OEQ distribué uniquement en test et toute question `train`/`validation` dont la forme normalisée apparaît dans un test.
- Conserver les bonnes réponses de QCM comme contenu documentaire, jamais comme niveau de triage.
- Émettre une file v2 distincte et maintenir `training_eligible: false`, `triage_level: null` et `split: null`.

## Alternatives écartées

- **Conserver MEDIQA 2019 sous le nom MediQAl :** rejeté, car ce sont deux datasets différents.
- **Réécrire la preuve v1 :** rejeté, car cela détruirait la traçabilité de la première génération.
- **Utiliser les tests pour atteindre le quota :** rejeté, car cela contaminerait l'évaluation.
- **Transformer les bonnes réponses en priorités de triage :** rejeté, car MediQAl n'annote pas cette tâche.

## Conséquences

La file v2 gagne 1 500 candidats bilingues ancrés dans MediQAl et conserve le volume total de 5 000. La source reste `candidate` : l'audit technique ne prouve ni absence complète de données personnelles, ni validité clinique, ni conformité RGPD définitive.
