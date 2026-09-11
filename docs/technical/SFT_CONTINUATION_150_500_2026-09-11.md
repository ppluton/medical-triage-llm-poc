# Reprise bornée du SFT général : 150 vers 500 étapes

- Date : 2026-09-11
- Statut : draft — version Kaggle 22 lancée, résultat en attente
- Sources : [plan figé](../../configs/sft-resume-150-to-500.json), [pilote v19](../evidence/SFT_V19_PILOT_RESULT_2026-09-11.md), [recharge v20](../evidence/SFT_V20_CHECKPOINT_RESULT_2026-09-11.md), [mémorisation v21](../evidence/SFT_MEMORIZATION_V21_RESULT_2026-09-11.md).

## Question

Après une mémorisation réussie sur douze exemples, mesurer la généralisation du SFT général après davantage d’exposition au corpus inchangé. Aucune garantie de gain n’est déduite du diagnostic de mémorisation.

## Contrat

Reprendre uniquement le checkpoint général v19 à 150 étapes, en vérifiant son résumé, les hashes de l’adaptateur, optimiseur, scheduler, RNG, trainer et scaler AMP. Les poids v21 de mémorisation sont exclus. Le corpus reste à 3 721 train, 479 validation ; zéro test utilisé. Seed, ordre, batch, accumulation, learning rate initial et horizon du scheduler de 1 000 étapes restent inchangés.

L’arrêt est fixé à **500 étapes au total**, soit 350 nouvelles étapes au maximum, ou **1 800 secondes de phase entraînement**, au contrôle de fin d’étape. À 500 étapes, environ 1,07 passage sur le train aura été effectué. Installation, recharge et évaluations initiale/finale sont supplémentaires ; le sous-processus est borné à 5 400 secondes.

Avant `train()`, les 30 générations du checkpoint 150 doivent être identiques à v19, avec une différence absolue de loss inférieure à 10⁻⁵ sur 479 validations. Avant la première mise à jour, le callback vérifie `global_step=150`, les états optimiseur à 150, le scheduler restauré exactement à 150, ses learning rates et le scaler identique. La politique standard de saut des batches déjà vus reste active. Cela ne constitue pas une preuve d’équivalence bit à bit avec une exécution GPU continue.

Les checkpoints 50/100/150 du pilote initial sont préservés dans une sortie distincte. Les nouvelles sauvegardes sont dans `source-sft-v2-continuation-500`, avec jusqu’à quatre checkpoints intermédiaires conservés. Le vrai `base.json` initial est copié après la fin ; la recharge initiale est explicitement `resume_start.json`, jamais appelée Base.

## Évaluation et décision

Même 479 références de loss et mêmes 30 générations greedy, cap 512 tokens. Comparer Base, 150 et fin de reprise par source : loss, terminaison, répétitions et accord aux réponses sources. Les 30 prompts restent un jeu de développement utilisé plusieurs fois ; ils ne représentent pas une évaluation finale indépendante.

La fin du budget n’autorise ni poursuite automatique, ni DPO, ni conclusion clinique. Si le temps expire avant 500, conserver et rapporter l’étape réelle. Si une assertion de restauration échoue, arrêter sans mise à jour et documenter l’échec.

## Preuve de lancement et vérifications

La [version 22](../evidence/SFT_CONTINUATION_V22_LAUNCH_2026-09-11.json) a été envoyée dans le notebook privé autorisé. Le CLI rapporte `RUNNING`. Cela prouve le lancement, pas encore la restauration GPU ou une mise à jour réussie.

Onze tests ciblés passent, notamment le refus des mauvais checkpoints/budgets et la distinction entre Base et reprise dans le rapport. Le préflight local valide l’archive générale réelle et les 3 721/479 lignes figées ; le notebook reconstruit les fichiers exactement et son Python est analysé sans erreur. Ruff et le contrôle de diff passent. La suite locale complète a obtenu le créneau partagé et terminé avant la demande d’arrêt : `val_390a682bd5ca`, **122 tests réussis en 4,57 secondes**, avec une dépréciation Starlette/httpx. Le statut terminal est `completed`, code 0.

La synthèse après téléchargement utilisera `scripts/summarize_sft_pilot.py` avec les arguments habituels et `--continuation-plan configs/sft-resume-150-to-500.json`. Elle publiera les métriques de Base et de fin, ainsi que celles de `resume_start` sous une clé distincte. La restauration et la qualité restent à établir dans les sorties v22.
