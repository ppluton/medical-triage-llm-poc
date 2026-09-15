# Démarrage vLLM v30 : échec de liaison CUDA

Date : 2026-09-13 — Statut : draft

## Sources et environnement

Notebook privé `pierrepluton/chsa-source-sft-qwen3`, version 30, GPU T4, code `a6ed200`. Statut terminal observé avec `kaggle kernels status` : `KernelWorkerStatus.ERROR`.
Journal récupéré avec `kaggle kernels output pierrepluton/chsa-source-sft-qwen3/30 -p artifacts/kaggle/vllm-api-v30-reports --file-pattern '.*\.log$'`.
SHA-256 du journal `vllm-api-v30/vllm.log` : `6211d98acde247a759acd164e26f24440c7f7eb921866fe0c68680ffd7e90130`.

## Résultat observé

Les environnements isolés ont permis de lancer vLLM 0.15.0. Le modèle Qwen3-1.7B-Base a été chargé en float16 : 3,25 GiB annoncés, 9,72 GiB disponibles pour le cache KV. Le moteur a sélectionné FLASHINFER sur T4. La compilation de son opération de préremplissage échoue lors de la liaison : `/usr/bin/ld: cannot find -lcuda: No such file or directory`. Le processus moteur puis le serveur quittent avant disponibilité.

## Portée et suite

Ce résultat prouve le chargement du modèle de base en mémoire GPU, pas une inférence, le chargement effectif des deux adaptateurs ni le fonctionnement de l’API. Aucune mesure de qualité ou de latence API n’est disponible pour ce run. Aucun entraînement supplémentaire n’a eu lieu.

La prochaine correction doit traiter le chemin de liaison vers la bibliothèque du pilote CUDA, ou sélectionner un backend compatible documenté. Il ne faut pas modifier les données ou les poids sur la base de cet échec d’environnement.

## Correctif préparé pour v31

Le runner recherche `libcuda.so.1` dans le cache `ldconfig`, crée un lien `libcuda.so` dans son propre répertoire de sortie et ajoute ce répertoire à `LIBRARY_PATH` en préservant la valeur existante. Aucun fichier système n’est modifié. L’absence du pilote provoque un échec explicite.

Validation locale : Ruff et génération du notebook passent ; contrôle ciblé avec cache de pilote simulé vérifiant découverte, résolution du lien, conservation du chemin et rejet du pilote absent. Le premier contrôle a rencontré la normalisation `/private` des chemins temporaires macOS ; l’assertion a été corrigée pour comparer les chemins résolus. Ces contrôles ne prouvent pas la compilation GPU.
