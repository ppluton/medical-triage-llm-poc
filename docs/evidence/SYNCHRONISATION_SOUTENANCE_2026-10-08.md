# Synchronisation documentaire de la soutenance

Date : 2026-10-08 — Statut : `draft`

## Périmètre et sources

Comparaison du paquet remis `POC_Agent_IA_triage_medical_Pluton_Pierre.zip`, du rapport PDF de 20 pages, de la présentation de 14 diapositives et des sources `reports/` de `main` à la révision `8239953690c120254df19d487a21c4f61bffda63`.

## Résultat de la revue

Les chiffres structurants concordent : 4 700 paires SFT (3 721/479/500), 426/54 paires DPO, SFT v39 puis DPO v41, 5/30 réponses exactes pour SFT et DPO, et 0/18 JSON conformes dans la réserve finale du SFT retenu. La preuve API antérieure (13/18 sorties SFT corrigées ou remplacées) demeure distincte de cette réserve.

Corrections documentaires :

- L’index des livrables mentionne la publication Hugging Face déjà documentée et les noms exacts des fichiers remis.
- Les notes précisent qu’un modèle Base n’est pas spécifiquement adapté au suivi de consignes, sans déclarer toute réponse impossible.
- La conclusion présente les règles comme restant à valider cliniquement.
- Le frontend est indépendant du GPU, sans promesse de disponibilité permanente.
- Le minutage suit les 14 diapositives, avec démonstration puis ouverture RAG, pour une cible de 14 min 30.

## Contrôles et limites

Relecture des écarts documentaires et `git diff --check`. La copie PowerPoint corrigée et les supports personnels restent hors Git ; le paquet initial reste conservé séparément. Le rapport et les résultats expérimentaux sont inchangés.

Cette synchronisation n’est ni une nouvelle expérience, ni une validation clinique, ni une preuve de disponibilité actuelle du service. Elle ne modifie aucun code, poids, dataset ou déploiement. Le minutage doit encore être vérifié par répétition orale.

## Sources

- [Rapport technique](../../reports/RAPPORT_TECHNIQUE_POC.md)
- [Présentation et notes](../../reports/PRESENTATION_POC.md)
- [Livrables](../../reports/LIVRABLES.md)
- [Fiche de soutenance](../../reports/FICHE_SOUTENANCE.md)
