# Comparaison Base/SFT avec définitions explicites — v26

- Date : 2026-09-12
- Statut : draft — version 26 acceptée par Kaggle, état RUNNING vérifié
- Sources : [consigne corrigée](TRIAGE_SHARED_PROMPT_2026-09-12.md), [mesure v25](TRIAGE_V25_RESULT_2026-09-12.md).

Notebook privé `pierrepluton/chsa-source-sft-qwen3`, T4 gratuite, image et dépendances
identiques à v25. Poids Base et SFT 500 inchangés. Dix-huit scénarios synthétiques
FR/EN identiques ; trente QA de validation pour contrôler la recharge. Zéro entraînement,
zéro exemple du test final. Seule la consigne de triage change pour fournir explicitement
les définitions du protocole pédagogique proposé. Aucune correction des sorties.

Le notebook généré fait 31 140 octets, SHA-256
`0e91d49e04448b644641549b9c1cc30a8cb764d1f1206b767ec5b64b509ea50d`.
Le bootstrap compile et Ruff passe. Le résumé enregistrera la version et le texte
exact de la consigne ; sorties attendues `triage-base-sft-v26/`.

```sh
PYTHONPATH=src python scripts/build_kaggle_triage_probe.py \
  --output artifacts/kaggle/triage-v26-launch \
  --metadata artifacts/kaggle/continuation-v22-launch/kernel-metadata.json
kaggle kernels push -p artifacts/kaggle/triage-v26-launch
kaggle kernels status pierrepluton/chsa-source-sft-qwen3
```

Le push a répondu « Kernel version 26 successfully pushed » ; le contrôle suivant
indiquait RUNNING. Cela ne prouve ni la fin de l'évaluation ni un gain de qualité.
Les poids SFT source sont recopiés en sortie avant inférence pour préserver l'archive.
