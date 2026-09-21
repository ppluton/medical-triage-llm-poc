# Vérification du support de soutenance v46

- Date : 2026-09-16
- Statut : verified_local_candidate
- Source de génération locale : `.codex-presentation-v43-build/build_deck.mjs`
- Sortie locale : `output/pptx/poc-triage-medical-chsa-v46.pptx`
- SHA-256 : `fd8db31a76141448fb10d98e08e7a075a5866dd179f2f4c85b33ca8508c80844`

Le support comporte dix slides et quatre graphiques natifs modifiables. La validation
structurelle ne signale aucun débordement ni élément hors page. Les dix slides ont été rendues
en images ; les slides inchangées avaient déjà été contrôlées dans la version précédente et
les slides 6, 7, 9 et 10, modifiées pour les résultats v43/v46, ont été réinspectées. Aucun
chevauchement, texte coupé ou problème de lisibilité n'a été observé.

Le support présente le DPO comme une optimisation exécutée mais non retenue, puis le résultat
de réserve v46 comme un échec du modèle brut au contrat de triage. La conclusion limite le POC
à une chaîne gouvernée avec garde-fous et décision humaine. Il ne revendique ni validation
clinique ni disponibilité cloud.

Cette preuve établit l'existence, l'éditabilité et la lisibilité du candidat local. Elle ne
prouve ni une soutenance réalisée, ni un parcours cloud accessible, ni une performance
clinique. Le fichier reste hors Git ; son empreinte et cette vérification sont versionnées.
