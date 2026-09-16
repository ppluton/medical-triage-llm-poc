# Ressource privée Kaggle de l’adaptateur DPO v41

- Date : 2026-09-16
- Statut : vérifiée et prête
- Statut clinique : aucune validation clinique
- Manifeste : `data/manifests/dpo-v41-kaggle-private-v1.json`

## Résultat observé

La ressource privée `pierrepluton/chsa-dpo-v41-policy-ae66169e-apache2`
(Kaggle dataset `12041763`) est au statut distant `ready`. La métadonnée distante
confirme le propriétaire `pierrepluton`, le caractère privé et la licence
`apache-2.0`.

Le lot contient uniquement l’adaptateur de politique final, le snapshot de tokenizer et
template, le résumé agrégé du run et les contrôles de poids. Le checksum SHA-256 du poids
principal est `ae66169e4a52077803fc5403bf088bf599f7813f86e5ec3cdb82df584fd4b565`,
identique à la preuve DPO v41.

## Incident de métadonnée conservé

Une première ressource privée, `pierrepluton/chsa-dpo-v41-policy-ae66169e`, a été créée
avec une valeur de licence que Kaggle a normalisée en `unknown`. Une nouvelle version n’a
pas modifié ce champ distant. Cette ressource est donc conservée comme historique mais
explicitement supersédée et ne doit pas être attachée aux futurs notebooks.

## Ce que cette preuve établit

- l’adaptateur DPO peut être remonté sans dépendre d’une ancienne sortie de notebook ;
- la ressource utilisable est privée, prête et porte la licence attendue ;
- aucun corpus, paire de préférence, prompt, sortie générée ou état d’optimiseur n’a été
  inclus dans le lot.

Elle ne prouve ni qualité de triage, ni sûreté clinique, ni ouverture correcte par vLLM.
Ces points restent couverts par les comparaisons et la démonstration séparées.
