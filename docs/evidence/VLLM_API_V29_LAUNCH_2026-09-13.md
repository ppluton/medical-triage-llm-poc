# Lancement de l'intégration vLLM / API — v29

- Date : 2026-09-13
- Statut : draft — version acceptée, résultats en attente
- Sources : scripts/run_vllm_api_demo.py, scripts/build_kaggle_vllm_demo.py, API et scénarios synthétiques versionnés.

## Périmètre

Notebook privé `pierrepluton/chsa-source-sft-qwen3`, T4 gratuit autorisé.
La v28 était COMPLETE avant le push. La CLI confirme « Kernel version 29 successfully pushed ».
SHA-256 du notebook : `c043be46d75c0ebb58e4225a2fe9037a4ba02b738eae8e70322ed994857cf305`.

vLLM 0.15.0 est installé dans un environnement séparé de l'API. Les deux adaptateurs
sauvegardés sont contrôlés par hash. Le serveur FP16 annonce SFT et DPO via LoRA.
La factory API authentifiée appelle ce vrai serveur, puis 18 scénarios synthétiques
sont mesurés pour chaque adaptateur. Les erreurs restent dans les rapports ;
le rapprochement des réponses et de l'audit est exécuté. Les processus démarrés
par le script sont arrêtés dans un bloc finally. Les deux archives de poids sont
recopiées pour préserver les entrées du prochain run privé.

## Vérification et limites

Ruff et CLI help passent ; bootstrap généré compilé localement. L'arrêt du groupe
d'un processus synthétique créé pour ce contrôle est vérifié. Aucun modèle n'a
été exécuté localement dans cette étape. L'installation, le démarrage vLLM, les
réponses, latences et audits restent à constater dans le résultat GPU.

Écoute limitée à 127.0.0.1 dans le notebook, sans tunnel ni port public. Ce n'est
pas encore l'endpoint cloud accessible demandé par le mandat. Aucun entraînement,
aucun test réservé ni validation clinique. La configuration FP16 avec JSON contraint
diffère de v28 ; ne pas confondre intégration, format et pertinence.
