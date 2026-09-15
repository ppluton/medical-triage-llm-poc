# Contrôle de recharge et comparaison de triage — v24

- Date : 2026-09-12
- Statut : draft — version 24 terminée en erreur au contrôle de recharge
- Sources : [échec v23](TRIAGE_V23_LAUNCH_2026-09-12.md), [runner](../../scripts/run_triage_probe.py).
- Environnement : notebook privé `pierrepluton/chsa-source-sft-qwen3`, T4 gratuite ; mêmes dépendances et checkpoint v22 que v23.

## Hypothèse et modification bornée

Unsloth était importé après PEFT/Transformers dans v23, contrairement au script SFT.
Les logs avertissent que cet ordre empêche certaines optimisations. La v24 rétablit
l'ordre du SFT. Elle conserve aussi les tokens observés et attendus après chaque
contrôle, pour rendre une éventuelle divergence analysable. Aucun poids, prompt,
corpus, hyperparamètre de génération ou seuil de réussite n'est modifié.

Cette hypothèse n'est pas encore validée. Les autres différences de chemin
d'inférence, notamment le remplacement des poids après génération Base, restent
à examiner si le contrôle échoue de nouveau. Il ne faut pas attribuer l'erreur aux
données sans preuve.

## Preuves locales et lancement

Trois tests ciblés passent (dont différences de tokens, préfixe tronqué et égalité),
Ruff et compilation du bootstrap passent. Ce sont des preuves du diagnostic local,
pas de reproductibilité GPU. L'ancien contrôle d'égalité stricte reste présent.

```sh
PYTHONPATH=src python scripts/build_kaggle_triage_probe.py \
  --output artifacts/kaggle/triage-v24-launch \
  --metadata artifacts/kaggle/continuation-v22-launch/kernel-metadata.json
kaggle kernels push -p artifacts/kaggle/triage-v24-launch
kaggle kernels status pierrepluton/chsa-source-sft-qwen3
```

La CLI confirme `Kernel version 24 successfully pushed`, puis `RUNNING`.
Notebook : 29 930 octets ; SHA-256
`8d64fa7b6b21f645cacabda508c4cce1df62c34f2be640e4aaa13b232490a941`.
Sorties attendues dans `triage-base-sft-v24/`. Zéro entraînement et zéro utilisation
du jeu de test. Le checkpoint v22 est recopié en sortie avant le contrôle.

## Décision suivante

Si les trente réponses sont reproduites, terminer les dix-huit scénarios et
analyser les résultats Base/SFT. Sinon, exploiter les divergences sauvegardées
avant une autre modification. Aucun DPO ni nouveau SFT long n'est lancé ici.

## Résultat terminal

La v24 a terminé en erreur, avec 14/30 séquences identiques, comme v23.
Les quinze réponses EN et une FR diffèrent. Les séquences détaillées sont
archivées hors Git ; le [résumé sans texte](TRIAGE_V24_RESULT_2026-09-12.json)
conserve leurs empreintes et la position des premières divergences.
L'import Unsloth en premier n'a donc pas suffi à résoudre le problème.
Aucune comparaison de triage SFT n'a été exécutée.

Le code source public d'Unsloth conserve des copies `_fast_lora` pour le décodage
et sa méthode `for_training` les supprime. Le script SFT effectue cette transition
entre évaluations ; notre évaluateur v24 ne le faisait pas avant remplacement des
poids. Cette observation motive une mesure explicite du cache dans v25, pas une
affirmation anticipée de correction. La lecture de la branche amont `main` ne
remplace pas la vérification du comportement dans la version GPU épinglée.

Sources techniques consultées le 12 septembre :
[cache d'inférence](https://github.com/unslothai/unsloth/blob/main/unsloth/kernels/utils.py),
[réinitialisation](https://github.com/unslothai/unsloth/blob/main/unsloth/models/llama.py).
