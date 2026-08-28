# Étape 1 — Comprendre la gouvernance des sources

- **Date :** 2026-08-28
- **Statut :** draft
- **Source technique associée :** [`../governance/REGISTRE_SOURCES_DONNEES.md`](../governance/REGISTRE_SOURCES_DONNEES.md)

## Ce que nous avons fait

Nous avons établi un registre initial des quatre datasets prescrits par la mission : MEDIQA 2019, FrenchMedMCQA, MedQuAD et UltraMedical-Preference. Pour chacun, nous avons relevé la source de référence, la licence affichée, le rôle possible dans le POC et les vérifications nécessaires avant un téléchargement.

Nous n'avons téléchargé ni exécuté ni transformé de données. C'est volontaire : une étape de gouvernance précède tout traitement de données médicales.

## Pourquoi nous l'avons fait

Un dataset n'est pas simplement un fichier à entraîner. Il détermine ce que le modèle peut apprendre, ce que l'on peut légalement publier et la valeur des mesures obtenues.

Dans ce POC, les quatre sources ont des formes différentes : QCM français, questions-réponses médicales, tâches QA/RQE et paires de préférences. Les mélanger sans comprendre leur origine pourrait créer une fausse impression de qualité ou faire fuiter des exemples d'évaluation vers l'entraînement.

La licence est une première condition d'usage, mais elle ne répond pas seule aux questions de provenance, de données sensibles, de droit d'auteur des contenus d'origine, de pertinence clinique et de reproductibilité.

## Comment nous l'avons fait

1. Lecture des pages de référence publiées par les détenteurs ou curateurs des datasets.
2. Consignation de la licence affichée et du type de contenu, sans inférer une autorisation plus large.
3. Identification des risques propres à chaque source : contenu d'examen, réponses retirées pour droit d'auteur, données de préférence synthétiques et schéma à contrôler.
4. Définition de sept critères d'acceptation qui devront être satisfaits avant toute ingestion.

## Notions à retenir

- **Provenance :** savoir d'où vient une donnée, sous quelle version et avec quelles transformations.
- **Révision immuable :** un commit Git ou SHA Hugging Face précis. Une branche `main` ou `master` peut changer et n'est pas suffisante pour reproduire un résultat.
- **Data card :** document décrivant les données, leur création, leurs limites, leurs licences et leurs usages prévus.
- **Ingestion :** entrée effective d'un dataset dans le pipeline local. Elle ne doit venir qu'après validation.
- **Fuite de données :** utilisation, même indirecte, d'un exemple de test pendant l'entraînement ou le réglage. Elle rend les résultats de test peu fiables.

## Ce que le résultat prouve et ne prouve pas

Cette étape prouve que nous avons identifié les sources et posé des garde-fous documentés avant manipulation. Elle ne prouve pas que les datasets sont juridiquement ou cliniquement validés, sans PII, ni directement adaptés au triage.

## Questions ouvertes et prochaine étape

La prochaine étape est de définir le schéma de métadonnées et le manifeste qui permettront de tracer chaque fichier, chaque transformation et chaque split. Avant tout téléchargement, nous épinglerons les révisions exactes et déciderons quelles sous-parties sont admissibles.
