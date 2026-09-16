# Vérification du candidat PDF v46 après préparation Modal et CI

- Date : 2026-09-16
- Statut : `verified_local_candidate`
- Source : `reports/RAPPORT_TECHNIQUE_POC.md`
- Sortie locale : `output/pdf/rapport-technique-poc-chsa-v46-ci-ready.pdf`
- SHA-256 : `389490c1c6d6dd789357e0d3134d5b30993eaf0ab182207d6db190a403bd4b04`

Le candidat comporte cinq pages A4. Les cinq pages ont été rendues après la régression de
240 tests puis inspectées visuellement. Aucun chevauchement, texte coupé, artefact noir ou
tableau illisible n'a été observé. Le pied de page rappelle le statut pédagogique et
l'absence de validation clinique.

Par rapport au candidat précédent, la section de déploiement décrit la définition Modal v1,
la séparation des environnements vLLM/API, le rehash des poids, l'audit synchronisé et la CD
manuelle. Elle ajoute la CI GitHub distante passée sur la PR #4 et précise qu'aucune ressource,
URL ou dépense Modal n'a été créée.

Cette preuve établit l'intégrité et la lisibilité du candidat local. Elle ne prouve ni le
build distant, ni le démarrage T4, ni le smoke test, ni la justesse clinique. Le PDF reste
hors Git ; sa source et son empreinte sont versionnées.
