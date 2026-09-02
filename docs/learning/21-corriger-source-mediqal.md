# Corriger une source ambiguë sans perdre la traçabilité

- **Date :** 2026-09-03
- **Statut :** draft
- **Sources :** ADR-006, carte de données MediQAl, audit local et preuve de génération v2

## Ce qui a été fait

La mention ambiguë « MediQA » a été résolue en faveur du dataset explicitement transmis `ANR-MALADES/MediQAl`. Le pipeline XML de MEDIQA 2019 a été remplacé par un lecteur JSONL MediQAl, puis la file complète de 5 000 candidats a été régénérée sous une nouvelle version.

## Pourquoi c'était nécessaire

MEDIQA 2019 et MediQAl sont deux corpus différents malgré leurs noms proches. Continuer à utiliser le premier aurait donné une provenance fausse. Réécrire la v1 aurait, inversement, effacé la preuve de ce qui avait réellement été produit auparavant.

## Comment cela a été réalisé

- révision Hugging Face épinglée et licence consignée ;
- inventaire text-free des 32 603 lignes ;
- mesure des recouvrements normalisés entre splits ;
- exclusion complète du test et de ses recouvrements ;
- résolution contrôlée des bonnes options MCQU/MCQM ;
- passage Presidio et recomplètement des quotas ;
- nouvelle file v2, nouvel index et nouveaux checksums.

## Notions à retenir

- Un nom de dataset n'est pas une identité suffisante : il faut un namespace et une révision.
- Un split déclaré par la source peut contenir des recouvrements textuels avec le test.
- Une bonne réponse à un examen apporte une connaissance médicale, pas une vérité de triage.
- Une correction de provenance doit créer une nouvelle version, pas altérer rétroactivement une preuve.

## Questions ouvertes

- Une déduplication sémantique doit-elle compléter le filtre lexical avant revue ?
- Quelle stratégie de revue humaine appliquer aux 56 rejets MediQAl et aux cas contenant des marqueurs de personne ou de lieu ?
- Quel protocole clinique approuvé convertira ensuite les scénarios rédigés en cibles de triage ?
