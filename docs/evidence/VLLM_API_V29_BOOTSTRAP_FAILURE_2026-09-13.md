# Échec d'amorçage v29 et correction v30

- Date : 2026-09-13
- Statut : draft — v29 échouée, v30 acceptée
- Sources : journal Kaggle v29, scripts/build_kaggle_vllm_demo.py.

La CLI indique ERROR pour v29. Le journal téléchargé dans
`artifacts/kaggle/vllm-api-v29-reports/chsa-source-sft-qwen3.log` indique un échec
de `python -m venv /tmp/chsa-vllm`, causé par le sous-processus `ensurepip`.
L'installation vLLM et les mesures n'ont pas été atteintes. Les archives SFT/DPO
avaient été recopiées auparavant ; elles restent disponibles à la version suivante.

Le bootstrap installe désormais virtualenv 20.35.4 depuis PyPI puis crée les deux
environnements avec cet outil. La version existe sur PyPI ; Ruff et compilation
du bootstrap passent. La commande de push du paquet `vllm-api-v30-final` renvoie
« Kernel version 30 successfully pushed ». Même notebook privé et T4 gratuit,
aucun entraînement, aucun accès public. L'exécution corrigée n'est pas encore prouvée.
