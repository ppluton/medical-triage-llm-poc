# Paquet vLLM/API v37 avec garde-fous

- Date : 2026-09-16
- Statut : prepared_not_launched
- Résultat compact : [JSON compagnon](VLLM_V37_PACKAGE_2026-09-16.json)
- Cible prévue : notebook Kaggle privé `pierrepluton/chsa-source-sft-qwen3`, T4
- Statut clinique : aucune validation clinique.

## Objectif

Préparer une régression GPU Base/SFT/DPO avec la nouvelle chaîne d'inférence, sans modifier
les poids et sans lancer un nouvel entraînement.

## Contenu vérifié

Le constructeur a créé `api-guardrails-v37` avec 47 fichiers embarqués. Le payload a été
décodé localement puis comparé au checkout : zéro divergence. Le bootstrap compile et porte
le nom de run attendu. Le notebook est configuré comme privé sur `NvidiaTeslaT4`.

La charge embarquée contient :

- API 0.4.0 et audit versionné ;
- prompt `triage-demo-v6-proposed` ;
- `proposed-guardrails-v1` ;
- les mêmes adaptateurs SFT et DPO contrôlés par empreinte ;
- les 18 scénarios synthétiques de développement et les dialogues de collecte ;
- une synthèse text-free `model_output` / `corrected` / `safe_fallback` reliée à la version
  du garde-fou pour chaque variante.

Empreinte du notebook :
`ee5c9f37fc0a720d1ed443ccc78fda9fdaa51e80d7c7039aa7f6c738331b1a80`.

## Vérification locale

Les tests ciblés du résumeur, des garde-fous et du service passent : 21 tests, avec le seul
avertissement externe Starlette/httpx déjà connu. Ruff passe sur le builder, le runner et
les tests. Le bootstrap du notebook compile après décodage. La régression complète
`val_9f3a8faa9c28` passe 199 tests en 15,13 secondes avec le même avertissement externe.

## Limites et prochaine preuve

Le paquet n'a pas encore été envoyé ni exécuté sur Kaggle. Il ne prouve donc ni le chargement
GPU, ni la génération avec le prompt v6, ni la présence effective des nouveaux champs dans
les audits distants. Une exécution réussie restera une intégration privée en boucle locale,
pas l'endpoint cloud extérieur demandé par la mission.

Après lancement, il faudra récupérer le dossier `api-guardrails-v37`, vérifier les codes de
sortie, rapprocher chaque réponse de l'audit, analyser le taux de fallback et refaire la revue
de contenu. Aucun gain clinique ne pourra être conclu à partir du seul statut des garde-fous.
