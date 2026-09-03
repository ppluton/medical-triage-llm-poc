# Construire un pilote de revue réellement représentatif

- **Date :** 2026-09-03
- **Statut :** draft
- **Sources :** file candidate v2, manifeste du pilote et schéma de revue

## Ce qui a été fait

Le premier lot séquentiel a été contrôlé avant revue. Ses 100 lignes appartenaient toutes à la famille `chest_pain`. Un second paquet a donc été sélectionné à partir de la file complète en conservant 50 groupes bilingues et en équilibrant proportionnellement les sources et les familles.

## Pourquoi c'était nécessaire

Un pilote doit permettre de découvrir des défauts variés. Un paquet limité à une seule famille pourrait donner une estimation trompeuse de la pertinence des sources, de la difficulté de rédaction et du risque PII.

## Comment cela a été réalisé

- vérification du SHA-256 de la file v2 avant lecture ;
- validation des 5 000 candidats contre leur schéma ;
- regroupement obligatoire des variantes FR/EN ;
- stratification croisée par source et famille de risque ;
- sélection déterministe à seed fixe ;
- création d'un formulaire local avec toutes les décisions à `pending` ;
- validation de chaque formulaire contre un schéma dédié.

## Notions à retenir

- Un découpage en lots n'est pas nécessairement un échantillonnage représentatif.
- Les deux langues d'un même scénario doivent rester ensemble pendant la revue et les futurs splits.
- Une revue technique de pertinence ne remplace pas une validation clinique.
- Un champ `pending` explicite est préférable à une approbation implicite ou automatique.

## Prochaine étape

Compléter les 50 formulaires avec un réviseur identifié, mesurer les taux de rejet et d'incertitude, puis décider si les règles de sélection et le protocole de rédaction doivent être modifiés avant de traiter les autres candidats.
