# Comprendre la baseline Qwen3 Base

- **Date :** 2026-08-31
- **Statut :** observed
- **Sources :** `docs/technical/BASELINE_SYNTHETIQUE_V1.md`, `docs/evidence/BASELINE_QWEN3_BASE_2026-08-31.md`

## Ce qui a été fait

Nous avons soumis huit scénarios synthétiques à Qwen3 Base, sans l’adaptateur LoRA. Le prompt demandait une réponse JSON très précise, puis le pipeline vérifiait la syntaxe et les champs obligatoires sans corriger la sortie du modèle.

## Pourquoi c’était nécessaire

Une amélioration après SFT n’a de sens que si l’on connaît le comportement initial du même modèle. Sans baseline, une sortie convaincante après entraînement ne permet pas de savoir si le SFT a réellement apporté quelque chose.

## Comment lire le résultat

Les huit sorties sont invalides. Le modèle Base a souvent répété des débuts d’objets commentés (`//{`) et n’a jamais fourni le JSON exigé. Ce résultat n’est pas un bug du parser : une API ne peut pas accepter un objet incomplet ou commenté comme du JSON valide.

Cela illustre la différence entre pré-entraînement et instruction following. Qwen3 Base sait compléter du texte, mais il n’est pas encore spécialisé pour suivre de façon fiable notre instruction et notre contrat de sortie. Le SFT doit précisément apprendre cette structure — sans que cela suffise à garantir la justesse clinique du contenu.

## À retenir

- Une baseline négative est utile : elle rend le besoin de spécialisation mesurable.
- Le post-traitement ne doit pas masquer les sorties invalides.
- Le futur checkpoint SFT devra être évalué avec le même prompt, le même parser et les mêmes scénarios.
- Un gain technique de conformité JSON ne sera pas une validation clinique.

## Question suivante

Le micro-run SFT sur un seul exemple a prouvé que l’entraînement fonctionne, mais il est trop petit pour conclure. Il faut maintenant préparer un dataset SFT gouverné plus substantiel avant une comparaison Base/SFT crédible.
