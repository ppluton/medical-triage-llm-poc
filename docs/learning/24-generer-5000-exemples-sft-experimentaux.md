# Générer 5 000 exemples sans inventer une validation clinique

- **Date :** 2026-09-03
- **Statut :** draft
- **Sources :** protocole expérimental v1, générateur SFT et preuve de génération

## Ce qui a été fait

La file de candidats non entraînables a été transformée en 5 000 scénarios synthétiques canoniques. Les labels sont produits par le protocole éducatif, les deux langues restent groupées et le test est isolé avant entraînement.

## Pourquoi plusieurs exécutions ont été nécessaires

La première génération contenait 168 doublons exacts de contexte et cible. L'ajout de variations structurées a réduit ce nombre à 4. Le générateur a alors été rendu fail-closed, puis une variation temporelle supplémentaire a permis d'obtenir zéro doublon.

Ces échecs intermédiaires sont utiles : ils montrent qu'un volume de 5 000 lignes ne garantit pas 5 000 exemples différents.

## Ce qui garantit la reproductibilité

- hash de la file candidate ;
- hash et identifiant du protocole dans chaque ligne ;
- code de génération et run ID ;
- assignation déterministe des splits ;
- schéma JSON de chaque enregistrement ;
- manifeste final sans texte médical ;
- checksum du dataset et des rendus Qwen3.

## Ce qui est réellement appris ici

Ce dataset vise surtout les comportements de sortie : structure JSON, niveaux autorisés, prudence, questions manquantes, signaux sévères explicites et avertissement. Les templates ne remplacent pas un corpus de scénarios rédigés ou revus par des cliniciens.

## Formulation à employer lors de la soutenance

« J'ai choisi de terminer la preuve de faisabilité avec un dataset synthétique protocolisé. J'ai conservé la provenance des corpus prescrits, mais je distingue cette provenance d'un véritable grounding sémantique. Les métriques mesureront l'apprentissage du protocole expérimental, pas une compétence clinique générale. »

## Étape suivante

Valider le pré-vol du run, exécuter un micro-entraînement reproductible, examiner la loss et quelques sorties hors test, puis décider si le run complet est pertinent.
