# Étape 6 — Évaluer un modèle de triage avant de l'entraîner

- **Date :** 2026-08-28
- **Statut :** draft
- **Source technique associée :** [`../technical/PROTOCOLE_EVALUATION_V1.md`](../technical/PROTOCOLE_EVALUATION_V1.md)

## Ce que nous avons fait

Nous avons codé les métriques qui compareront les sorties du modèle aux références du jeu de test : correspondance exacte, rappel des cas `maximum`, sous-triage, sur-triage et matrice de confusion.

## Pourquoi

Une accuracy seule peut masquer un problème grave : le modèle peut être souvent juste mais sous-prioriser un cas critique. Le projet doit donc isoler et compter ces erreurs avant toute conclusion sur SFT ou DPO.

## Comment

Nous représentons chaque cas par une priorité attendue et une priorité prédite. L'ordre `deferred < moderate < maximum` permet de déterminer si l'erreur va vers une priorité plus basse (sous-triage) ou plus haute (sur-triage).

## Ce que cela prouve et ne prouve pas

Les tests prouvent le calcul des métriques. Ils ne prouvent pas que les références sont médicalement correctes ni qu'un seuil clinique est atteint : ces éléments devront être définis et validés par des référents cliniques.
