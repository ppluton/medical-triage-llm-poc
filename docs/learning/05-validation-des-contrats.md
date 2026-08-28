# Étape 5 — Valider les contrats avant d'ingérer des données

- **Date :** 2026-08-28
- **Statut :** draft
- **Source technique associée :** [`../technical/VALIDATION_CONTRATS_V1.md`](../technical/VALIDATION_CONTRATS_V1.md)

## Ce que nous avons fait

Nous avons ajouté une validation automatique des JSON Schemas et un exemple synthétique conforme au contrat d'évaluation.

## Pourquoi

Un manifeste peut être complet en apparence mais être dangereux, par exemple s'il est déclaré `approved` alors que le contrôle PII n'a pas été exécuté. Le schéma devient une barrière automatique contre cette incohérence.

## Comment

Le module charge le schéma versionné, valide l'objet en mémoire et bloque dès qu'une règle est violée. Un test vérifie précisément qu'un manifeste `approved` avec `pii: not_run` est rejeté.

## Ce que cela prouve

La structure et une règle d'admission sont appliquées par le code sur des fixtures synthétiques. Cela ne prouve pas encore que les données externes passent ces contrôles.
