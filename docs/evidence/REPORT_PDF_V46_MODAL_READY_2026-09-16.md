# Vérification du candidat PDF v46 après préparation Modal

- Date : 2026-09-16
- Statut : `verified_local_candidate`
- Source : `reports/RAPPORT_TECHNIQUE_POC.md`
- Sortie locale : `output/pdf/rapport-technique-poc-chsa-v46-modal-ready.pdf`
- SHA-256 : `82346543c20abb2ea0c389648bbb909b9e6e32d98a5ce5d5afe2196a825ecac5`

Le candidat comporte cinq pages A4. Les cinq pages ont été rendues après la régression de
240 tests puis inspectées visuellement. Aucun chevauchement, texte coupé, artefact noir ou
tableau illisible n'a été observé. Le pied de page rappelle le statut pédagogique et
l'absence de validation clinique.

Par rapport au candidat précédent, la section de déploiement décrit la définition Modal v1,
la séparation des environnements vLLM/API, le rehash des poids, l'audit synchronisé et la CD
manuelle. Elle précise qu'aucune ressource, URL ou dépense Modal n'a été créée.

Cette preuve établit l'intégrité et la lisibilité du candidat local. Elle ne prouve ni le
build distant, ni le démarrage T4, ni le smoke test, ni la justesse clinique. Le PDF reste
hors Git ; sa source et son empreinte sont versionnées.
