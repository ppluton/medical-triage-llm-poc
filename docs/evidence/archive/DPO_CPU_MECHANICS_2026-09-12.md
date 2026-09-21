# Mécanique DPO sur un modèle miniature synthétique

- Date : 2026-09-12
- Statut : draft — preuve CPU ; entraînement du modèle médical non effectué
- Sources : `scripts/check_dpo_mechanics.py`, `artifacts/dpo-cpu-mechanics/result.json`.

Environnement isolé macOS Python 3.13, Torch 2.13.0, Transformers 4.57.6,
TRL 0.23.1, PEFT 0.18.1, Accelerate 1.14.0, Datasets 4.3.0.
Job `val_d72fd56095f1`, exit 0, terminé et slot libéré ; processus 94292 absent.

Un Qwen3 aléatoire miniature (une couche, hidden_size 32, LoRA r2 q/v) utilise
le tokenizer SFT figé, avec deux préférences synthétiques de couleur et répétition.
Deux étapes CPU FP32, learning rate 5e-4, sans quantification et sans données médicales.
Les quatre tenseurs policy changent ; les quatre tenseurs reference restent identiques.
Temps trainer observé : 0,0918 s, loss 0,6931584 ; durée du job environ 51,5 s,
principalement chargement/imports. La loss ne constitue pas une mesure de qualité.

Commande exécutée via codex-validate :
`env PYTHONPATH=src TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 artifacts/dpo-cpu-runtime/bin/python artifacts/dpo-cpu-mechanics/check.py`.
Le script exécuté est conservé hors Git ; sa copie versionnée, seulement formatée,
est `scripts/check_dpo_mechanics.py`. Ses chemins de sortie sont réservés à ce diagnostic,
pas au modèle médical. Ne pas confondre le checkpoint miniature et le SFT général.

Prouvé : fonctionnement local du DPOTrainer avec deux adaptateurs, initialisation
identique et référence inchangée à la fin. Non prouvé : précision FP16/quantification
CUDA, mémoire T4, qualité médicale, données DPO approuvées, sauvegarde/recharge du
futur adaptateur médical. Aucun score de ce diagnostic ne figure dans la comparaison
Base/SFT/DPO du projet.
