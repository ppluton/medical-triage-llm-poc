# Lire correctement le micro-run SFT

- **Date :** 2026-09-04
- **Statut :** observed
- **Sources :** configuration et preuve du micro-run SFT source-derived

## Ce qui a été fait

Qwen3-1.7B Base a reçu un adaptateur LoRA et a exécuté 20 étapes sur le vrai dataset source-derived. Le train a été mélangé avec une seed fixe et la validation du smoke test contient les trois sources. Le test n'a pas été chargé.

## Pourquoi commencer par 20 étapes

Un run court détecte les problèmes de format, de mémoire, de template, de longueur de séquence et de sauvegarde avant de consacrer plusieurs heures à un entraînement complet. Il répond à la question « la chaîne fonctionne-t-elle ? », pas à « le modèle est-il meilleur ? ».

## Comment lire les losses

La train loss et l'eval loss sont calculées, mais vingt étapes ne suffisent pas pour juger la convergence. Une eval loss inférieure à la train loss sur ce run peut venir du petit échantillon de validation, du dropout nul, du mélange des longueurs ou de la difficulté différente des exemples. Ce n'est pas une preuve de généralisation.

## Notions à retenir

- le dataset complet disponible n'est pas équivalent au nombre d'exemples effectivement vus en 20 étapes ;
- une validation de 50 lignes est un smoke test, pas l'évaluation finale ;
- une loss mesure la prédiction de tokens, pas la qualité du triage ;
- seule une comparaison Base/SFT/DPO sur le même test permet d'attribuer un gain au post-entraînement ;
- la validation clinique reste une catégorie de preuve différente.

## Formulation pour la soutenance

« Le micro-run source-derived a validé l'exécution de bout en bout sur mon matériel : chargement, tokenisation, LoRA, entraînement, validation et sauvegarde. Je ne présente pas ses losses comme une performance finale. Elles servent à décider la configuration du run complet. »
