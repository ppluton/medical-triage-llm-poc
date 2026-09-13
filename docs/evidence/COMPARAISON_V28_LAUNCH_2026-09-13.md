# Lancement de la comparaison Base / SFT / DPO v28

- Date : 2026-09-13
- Statut : draft — version 28 acceptée par Kaggle, résultats en attente
- Sources : notebook généré par `scripts/build_kaggle_current_comparison.py`, réponse Kaggle CLI et [contrôle DPO](DPO_V27_ARTIFACT_CHECK_2026-09-13.json).

## Périmètre et méthode

Notebook privé `pierrepluton/chsa-source-sft-qwen3`, T4 gratuit autorisé.
Comparaison commune : 479 exemples de validation QA, 30 générations QA et
18 scénarios synthétiques de développement, pour Base, SFT 500 et DPO v27.
Même runtime, mêmes prompts et paramètres pour les trois variantes.
Aucun pas d'optimisation ; jeu de test final inutilisé.

Commande : `kaggle kernels push -p artifacts/kaggle/current-comparison-v28-final`.
Retour : `Kernel version 28 successfully pushed`.
SHA-256 du notebook : `cd032885a8c938d61f3f656241aea7bdebf4cb25aa8492f6f3b6e1c2895b9ab7`.

## Préconditions et limites

Les poids DPO téléchargés ont passé le contrôle local de correspondance exacte
avec les empreintes du run. Le contrôle est également exécuté au démarrage GPU.
Le tokenizer conserve les mêmes fichiers de vocabulaire et de template après
sauvegarde dans le runtime DPO. Le lancement accepté ne prouve ni la fin de
l'évaluation, ni un gain de qualité, ni une validation clinique.
La prochaine décision dépend des résultats comparables, encore indisponibles.

## Observation de progression

Le 2026-09-13, la page Kaggle du run `349471067` affiche
`{"stage": "base", "loss_records": 450}` ; la CLI confirme RUNNING.
Le runner publie ce message après 450 calculs de loss terminés avec des valeurs finies.
Cela établit le passage du contrôle des artefacts et du chargement des deux
adaptateurs dans ce processus. Cela ne prouve pas encore la fin des 479 exemples,
les générations, ni la comparaison SFT/DPO. La CLI de téléchargement ne fournit
pas encore de journal exporté pour cette version active ; observation faite dans
le panneau du run, sans lancer de session interactive supplémentaire.
