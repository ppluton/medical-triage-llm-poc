# Invalidation du cache LoRA et comparaison de triage — v25

- Date : 2026-09-12
- Statut : draft — version 25 acceptée, observée RUNNING ; résultat GPU en attente
- Sources : [échec v24](TRIAGE_V24_LAUNCH_2026-09-12.md), `scripts/run_triage_probe.py`, `tests/test_triage_probe.py`.
- Environnement : notebook privé `pierrepluton/chsa-source-sft-qwen3`, T4 gratuite,
  mêmes versions et poids SFT 500 que v24 ; aucun entraînement.

## Hypothèse testée

Après génération Base, les copies `_fast_lora` peuvent encore contenir les anciens
poids malgré le remplacement des tenseurs principaux par le checkpoint SFT.
Le chemin SFT connu appelle `for_training` entre évaluations ; v24 ne le faisait
pas. La v25 rétablit cette transition puis repasse immédiatement en inférence.
Aucun appel au trainer ni aucune étape d'optimisation n'est introduit.

Le fichier `adapter_reload.json` doit donner : nombre de caches et de copies
obsolètes avant/après chargement, égalité exacte des poids chargés avec le fichier,
puis absence de caches après réinitialisation. Le contrôle des trente réponses
reste strict et conserve ses sorties détaillées. Si une condition échoue, aucune
comparaison de triage SFT n'est déclarée complète.

## Preuves locales et artefact

Quatre tests ciblés passent, dont un test CPU avec de vrais tenseurs Torch montrant
la détection d'une copie FP16 devenue obsolète après changement du poids. Ruff et
compilation du bootstrap passent. Ces tests ne prouvent pas le correctif GPU.

Notebook : 30 525 octets ; SHA-256
`3ed1d4929b58ca8e2610ae4f6eaa940811d49983b79d36087541473624a5fe5b`.
Résumé v22 attendu :
`45d6c88ef5e17e150a38f5ca7593212619ff854febe10901635f98913a6edb75`.
Sorties prévues : `triage-base-sft-v25/`.

```sh
PYTHONPATH=src python scripts/build_kaggle_triage_probe.py \
  --output artifacts/kaggle/triage-v25-launch \
  --metadata artifacts/kaggle/continuation-v22-launch/kernel-metadata.json
kaggle kernels push -p artifacts/kaggle/triage-v25-launch
kaggle kernels status pierrepluton/chsa-source-sft-qwen3
```

L'archive SFT est recopiée avant inférence pour préserver le checkpoint. Aucun
jeu de test final n'est utilisé. Un succès éventuel doit encore être suivi de
l'analyse des réponses de triage ; il ne prouvera pas une qualité clinique.
