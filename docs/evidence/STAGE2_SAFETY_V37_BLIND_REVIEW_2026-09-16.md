# Revue qualitative aveugle v37

- Date : 2026-09-16
- Statut : revue de projet terminée ; aucune validation clinique
- Manifeste : [couverture v37](../../data/manifests/stage2-safety-review-v37-blind.json)
- Sources : sorties endpoint v37 privées, 18 scénarios synthétiques de développement

## Question

Après application des garde-fous, SFT ou DPO réduisent-ils clairement les affirmations
non étayées, diagnostics, recommandations dangereuses et corruptions de texte par rapport
à la Base ?

## Méthode

La file seed `137` masque l'identité Base/SFT/DPO. Le scénario contradictoire anglais est
exclu de la lecture comparative parce que la Base n'a pas produit de réponse complète ; son
échec `generation_length` reste compté séparément. Les 17 autres scénarios ont chacun trois
réponses, soit 51 décisions prises avant ouverture de la clé.

La grille reprend les quatre flags de l'ADR-016. La revue est assistée par Codex et ne
constitue pas l'avis d'un professionnel de santé.

## Résultats après démasquage

| Variante | Sorties signalées | Faits non étayés | Diagnostic/prescription | Délai dangereux | Corruption/répétition |
|---|---:|---:|---:|---:|---:|
| Base | 7/17 | 3 | 2 | 0 | 4 |
| SFT | 6/17 | 3 | 1 | 0 | 5 |
| DPO | 6/17 | 3 | 1 | 0 | 5 |

Les garde-fous évitent ici les recommandations de délai dangereuses observées avant leur
ajout. Ils ne suppriment pas les faits inventés ni les corruptions. SFT et DPO ont exactement
les mêmes comptes qualitatifs ; aucun bénéfice DPO sur le SFT n'est démontré. L'écart d'une
sortie entre Base et SFT ne suffit pas à attribuer un gain général, surtout sur un jeu vu de
17 scénarios.

## Décision d'entraînement

Un nouveau SFT est requis pour la **traçabilité du livrable** : le checkpoint historique
n'a pas été entraîné sur le corpus final v2.2 avec ses splits et contrôles de confidentialité.
Cette décision ne prétend pas que répéter la recette améliorera le triage. Le run conserve
Qwen3-1.7B-Base, LoRA et une configuration bornée ; il doit comparer validation et sorties
avant toute conclusion.

Le DPO sera rejoué seulement depuis le SFT v2.2 retenu afin de conserver une lignée cohérente.
Son résultat actuel sans gain reste la baseline négative ; aucun allongement opportuniste
n'est justifié sans métrique de préférence ou de sûreté qui progresse.

## Limites

Le jeu est un jeu de développement déjà consulté. Les références sont proposées et la revue
n'est pas clinique. Les comptes servent à décider de l'ingénierie et non à estimer un taux de
risque patient. Une nouvelle réserve gelée reste nécessaire pour l'évaluation finale.
