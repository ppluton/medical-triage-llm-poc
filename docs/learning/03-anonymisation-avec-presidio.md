# Étape 3 — Comprendre l'anonymisation avec Presidio

- **Date :** 2026-08-28
- **Statut :** draft
- **Source technique associée :** [`../technical/ANONYMISATION_V1.md`](../technical/ANONYMISATION_V1.md)

## Ce que nous avons fait

Nous avons écrit un premier module d'anonymisation de texte, des tests unitaires et une politique documentée. Il détecte des informations personnelles, les remplace par des jetons, puis effectue une seconde détection pour signaler les cas qui doivent être revus manuellement.

## Pourquoi nous l'avons fait

Les datasets médicaux peuvent contenir, même de façon inattendue, un nom, un email, un numéro de téléphone ou un identifiant de dossier. Il faut détecter ce risque avant d'entraîner ou d'évaluer un modèle. Le POC public doit également éviter de publier le texte de ces contrôles dans ses logs.

## Comment nous l'avons fait

1. Presidio `AnalyzerEngine` détecte les entités PII dans le texte français ou anglais.
2. `AnonymizerEngine` remplace chaque entité détectée par un jeton explicite, sans moyen de revenir au texte d'origine.
3. Le texte obtenu est analysé une seconde fois.
4. S'il reste une entité détectée, le statut est `manual_review_required`. Si le moteur échoue ou si la langue est inconnue, le traitement est bloqué.
5. Les tests utilisent des valeurs synthétiques et vérifient le remplacement, la réanalyse et l'absence de texte source dans l'audit.

## Notions à retenir

- **PII :** information permettant d'identifier directement ou indirectement une personne.
- **Détection :** repérer une PII n'est pas encore l'effacer ; c'est le rôle de l'analyseur.
- **Anonymisation non réversible :** remplacement qui ne permet pas de retrouver la valeur initiale.
- **Fail closed :** en cas d'erreur, on bloque le flux au lieu de laisser passer une donnée non contrôlée.
- **Faux négatif :** une PII qui existe mais n'est pas détectée. C'est pourquoi la revue humaine reste nécessaire.

## Ce que le résultat prouve et ne prouve pas

Les tests prouvent le comportement du module avec des détecteurs contrôlés et des données synthétiques. Ils ne prouvent pas encore le rappel réel de Presidio avec les modèles français et anglais, l'absence de PII dans un dataset externe ou une conformité RGPD.

## Prochaine étape

Installer les dépendances et les modèles spaCy du projet, puis exécuter un test d'intégration sur des scénarios synthétiques afin de mesurer ce que le moteur détecte réellement.
