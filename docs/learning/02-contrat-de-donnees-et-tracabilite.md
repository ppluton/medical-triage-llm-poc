# Étape 2 — Comprendre le contrat de données et la traçabilité

- **Date :** 2026-08-28
- **Statut :** draft
- **Source technique associée :** [`../technical/CONTRAT_DONNEES_V1.md`](../technical/CONTRAT_DONNEES_V1.md)

## Ce que nous avons fait

Nous avons défini un langage commun pour décrire deux choses : un fichier téléchargé depuis une source publique et un exemple après transformation pour le SFT, le DPO ou l'évaluation. Les deux JSON Schemas sont versionnés dans `data/manifests/`.

## Pourquoi nous l'avons fait

Sans contrat, il devient vite impossible de répondre à des questions simples mais essentielles : « quelle version de données a entraîné ce modèle ? », « cette réponse a-t-elle été anonymisée ? » ou « cet exemple de test est-il resté hors entraînement ? ».

Le manifeste traite la provenance d'un fichier. L'enregistrement transformé traite le parcours d'un exemple. Les séparer empêche de stocker des données médicales brutes dans la documentation Git tout en gardant une piste d'audit utile.

## Comment nous l'avons fait

1. Nous avons repris les champs minimaux de la spécification : langue, symptômes, antécédents, constantes, priorité et statut d'anonymisation.
2. Nous avons ajouté les champs nécessaires à la reproductibilité : version de schéma, source, licence, révision, hash de code, pipeline et run.
3. Nous avons distingué les données SFT, DPO et évaluation pour éviter de confondre une cible d'entraînement, une préférence et une vérité attendue de test.
4. Nous avons limité le contexte patient à des catégories et interdit les identifiants personnels.

## Notions à retenir

- **JSON Schema :** contrat lisible par un humain et vérifiable par une machine. Il indique les champs obligatoires, leur type et les valeurs autorisées.
- **Checksum SHA-256 :** empreinte qui permet de vérifier qu'un fichier téléchargé n'a pas changé.
- **Manifeste :** carte d'identité d'un fichier source ; ce n'est pas le fichier source lui-même.
- **Split :** séparation entre `train`, `validation` et `test`. Le test final ne sert pas à orienter les choix de modèle.
- **SFT et DPO :** le SFT apprend une cible de réponse ; le DPO apprend quelle réponse est préférable pour le même prompt.

## Ce que le résultat prouve et ne prouve pas

Les contrats sont définis et leur syntaxe JSON est vérifiée. Ils ne prouvent pas encore que les scripts de validation existent, qu'un dataset réel respecte le contrat ou qu'une réponse de triage est appropriée cliniquement.

## Question ouverte et prochaine étape

La prochaine étape est de définir le pipeline d'anonymisation et ses tests sur des exemples strictement synthétiques. Nous pourrons alors valider le contrat sur ces exemples sans introduire de données réelles.
