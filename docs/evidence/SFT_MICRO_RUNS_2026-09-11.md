# Micro-runs correctifs SFT — 11 septembre 2026

- **Date :** 2026-09-11
- **Statut :** draft
- **Sources :** ADR-011 ; audit du 5 septembre ; TERMINATION_MICRO_PROTOCOL_2026-09-11.json ; TERMINATION_MICRO_V15_RESULT.json ; SFT_V2_SMOKE_INPUTS.json.
- **Périmètre :** vérifier la terminaison, les poids entraînés et la sauvegarde/recharge avant tout nouveau run long. Aucun entraînement DPO ni test final.
- **Environnement :** notebook privé `pierrepluton/chsa-source-sft-qwen3`, T4 gratuit, une seule GPU visible par le processus, base `unsloth/Qwen3-1.7B-Base` révision `e249956c10337100486d07afb77e3eb2b30906b8`.

## v15 — isoler la correction EOS sur le corpus historique

La version 15 reprend le checkpoint SFT v5 inchangé. Elle utilise les mêmes 64 exemples train v1 et 3 validations sélectionnés par hash avec seed 42. La seule transformation du texte d'entraînement est le remplacement du terminateur de la dernière réponse par l'EOS natif. L'optimiseur est redémarré : les résultats ne séparent donc pas l'effet EOS de tout effet possible d'une continuation SFT. Aucun bras témoin avec 20 étapes supplémentaires au format initial n'a été exécuté.

Le run termine 20 étapes en **77,2572 secondes d'entraînement** (`train_loss=1,247474`). Le temps du notebook comprend en plus l'installation, le chargement, la compilation et les générations. Les versions effectives sont Unsloth 2026.8.22, Unsloth Zoo 2026.8.16, PyTorch 2.10.0+cu128, Transformers 5.5.0, TRL 0.23.1 et PEFT 0.18.1.

| Contrôle | Avant | Après | Après recharge |
|---|---|---|---|
| Tokens générés sur les 3 mêmes exemples | 256 / 256 / 256 | 20 / 67 / 10 | 20 / 67 / 10 |
| Fin par EOS | 0/3 | 3/3 | 3/3 |
| Plafond de 256 atteint | 3/3 | 0/3 | 0/3 |
| Fraction moyenne de 4-grammes de tokens répétés | 0,6456 | 0,0104 | 0,0104 |

La baisse de répétition est descriptive et dépend aussi de la longueur des réponses ; elle ne mesure pas une qualité clinique. Les **392 tenseurs LoRA** diffèrent des poids v5 et sont finis. Les 64 exemples du trainer ont chacun **un EOS natif supervisé**. Le tokenizer exporté conserve le rendu attendu sur les 67 exemples du contrôle. Le modèle est ensuite rechargé depuis une nouvelle base épinglée et les poids exportés : les listes de tokens générés sont identiques.

L'adaptateur v15 est récupéré localement hors Git et son SHA-256 est vérifié : `447edcacb652887cbf8ec1295311df0e0e290b8d12e3bdc16b8e7407c3de52af`. Les sorties détaillées sont archivées sous `artifacts/kaggle/termination-micro-v15/termination-micro-native-eos/`.

## Revue de contenu et portée de la preuve

- Sur la question française dont v1 avait supprimé les choix, la réponse après micro-run parle d'un syndrome sans rapport avec les choix sources de rétrocession de médicaments. **L'arrêt est corrigé, le contenu reste hors sujet.**
- Sur le QCM MediQAl, la combinaison produite après micro-run correspond à la réponse source.
- La réponse anglaise est lisible et s'arrête, mais contient des précisions absentes de la référence fournie. Aucune validation médicale de ces précisions n'est réalisée.

**Proven :** entraînement court effectif, EOS supervisé, arrêt sur trois exemples, export et recharge reproductibles dans le runtime Kaggle utilisé. **Non prouvé :** correction générale des réponses, qualité du corpus v2 en entraînement, comparaison complète Base/SFT, sûreté clinique et acceptation DPO. Le v15 n'est pas un checkpoint final.

## v16 — micro-test du corpus corrigé v2

Le protocole conserve la même base, le checkpoint initial v5, 20 étapes, seed 42, 64 train et 3 validations. Il ajoute les choix QCM du corpus v2. Le premier envoi de notebook a été refusé avant exécution : source supérieure à 1 Mo. Il n'a pas lancé de GPU. Le paquet transmis au notebook existant ne contient finalement que les 67 conversations sélectionnées, compressées, avec un manifeste de filiation et des hashes figés ; aucun nouveau dataset Kaggle n'est créé et le test final n'est pas inclus.

La sélection locale vérifie d'abord les hashes des fichiers complets v2 ; le runner distant vérifie ensuite les hashes et effectifs exacts du sous-ensemble. `--input-scope smoke` est distinct de `full` : on ne prétend pas avoir relu les 4 500 conversations sur la GPU. Les contrôles des fichiers complets restent ceux de l'audit local.

Le v16 termine 20 étapes en **68,4865 secondes d'entraînement**, avec 392 tenseurs modifiés et une recharge identique. Les trois réponses passent de 256/256/256 à **20/105/25 tokens**, toutes terminées par EOS. Les 64 labels EOS ont été contrôlés dans le trainer. L'adaptateur est archivé et vérifié par SHA-256 `c81453b0f2615b0fe19d0ebc0919d3f8e059595a033c1f3ccae99798a2e9877f`.

La revue des deux QCM montre toutefois des divergences avec les réponses sources : le premier sélectionne une autre proposition ; le second omet deux éléments de la combinaison attendue. Le contenu anglais ajoute encore des détails absents de sa référence. **La chaîne technique est prouvée sur ce micro-run, l'acceptation qualitative est refusée sur ces observations.** Voir [bilan v16](SFT_V2_MICRO_V16_RESULT.json).

## v17 — expérience contrôlée sur le périmètre de loss

Hypothèse proposée : la loss sur toute la conversation consacre une part du signal aux questions et aux choix incorrects. On teste une loss limitée à la réponse attendue, sans affirmer que cela explique à lui seul les erreurs de v16.

Le v17 repart du même v5, avec les mêmes 64+3 exemples v2, la même seed, le même optimiseur et les mêmes 20 étapes. Les chaînes complètes et les tokens sont conservés ; seul le masque de loss change. Le format standard prompt/completion et `completion_only_loss=True` suivent la [documentation officielle TRL 0.23.1](https://huggingface.co/docs/trl/v0.23.1/sft_trainer#train-on-completion-only). Aucun masque Jinja implicite n'est utilisé.

Avant entraînement, le runner exige pour chaque exemple : tokens identiques au rendu de référence, tous les labels du prompt à -100, tous les tokens de réponse supervisés, EOS compris. Les tests locaux refusent un prompt supervisé ou un EOS masqué. Le découpage exact a également été vérifié sur les 64 exemples réels avant l'envoi. L’audit du trainer GPU ci-dessous confirme ce masque.

Le v17 termine en **69,0176 secondes d'entraînement**, avec 392 tenseurs modifiés. L'audit GPU confirme les 64 prompts intégralement masqués et les 64 réponses intégralement supervisées, EOS compris. Les générations avant entraînement sont identiques token par token à celles de v16, ce qui vérifie le point de départ du contrôle. Après entraînement : **14/60/25 tokens, 3/3 EOS, recharge identique**, aucun 4-gramme répété sur ces trois sorties. Voir [bilan v17](SFT_V2_COMPLETION_V17_RESULT.json).

L’adaptateur v17 est archivé localement et son SHA-256 correspond au run : `060af1186c1e8c5932503d706eefb6a54b92c369eba3f117725cd3a72108e84d`. Le bilan JSON est enrichi par le contrôle des labels et la revue de concordance aux sources ; ces champs complètent le résumé automatique.

La qualité ne passe toujours pas : le premier QCM choisit une proposition différente de la référence ; le second omet les mêmes deux éléments que v16. Le texte anglais contient des précisions absentes de la référence. La baisse de loss, calculée sur un autre périmètre de tokens, ne se compare pas directement à la loss v16. Aucun gain qualitatif général n'est démontré.

**Prouvé sur le micro-run :** masquage, entraînement, terminaison et recharge. **Non prouvé :** qualité générale, sûreté clinique, aptitude au DPO. Le checkpoint v17 ne devient pas le modèle final. Aucun quatrième ajustement sur ces seuls trois exemples n'est prévu : l'étape suivante est une évaluation élargie et figée, sans utiliser le test final.

## Reproduction et contrôles locaux

```sh
PYTHONPATH=src python scripts/run_sft_termination_experiment.py \
  --train /path/to/train.jsonl --validation /path/to/validation.jsonl \
  --sft-adapter /path/to/archived-v5 --dataset-version v2 --input-scope smoke \
  --arm native-eos --output /path/to/fresh-output --dry-run

PYTHONPATH=src python scripts/summarize_termination_experiment.py \
  --run-directory artifacts/kaggle/termination-micro-v15/termination-micro-native-eos \
  --output /path/to/report.json
```

L'exécution CUDA utilise la même commande sans `--dry-run`, avec un timeout du processus de 1 200 secondes. La configuration effective et les versions sont archivées dans `summary.json`. Le bilan ne peut jamais autoriser automatiquement un run long : `full_training_approved=false`.

Validation locale finale de la pipeline : **106 tests passent**, une dépréciation Starlette/httpx sans échec, via `codex-validate` (`val_c70f7340fad2`). Les onglets temporaires de suivi v15 sont fermés ; la session de navigateur est libérée.

## Prochaine comparaison figée

Le [protocole v2 élargi](../../configs/qa-validation-v2-expanded-v1.json) réserve les 500 validations pour la loss et 30 nouveaux exemples pour les générations (15 FR, 15 EN), hors des trois diagnostics déjà inspectés. Il est **proposé, non exécuté** : le runner historique Base/SFT reste figé sur v1 et doit recevoir un chemin v2 explicite avant exécution. Aucun exemple test n'est utilisé. Les observations de ces micro-runs ne justifient pas un entraînement long ni le DPO.
