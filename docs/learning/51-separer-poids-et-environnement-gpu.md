# Séparer le cache des poids de l'environnement GPU

- Date : 2026-09-16
- Statut : draft
- Sources : [preuve de ressource Kaggle](../evidence/QWEN3_BASE_KAGGLE_RESOURCE_2026-09-16.md),
  [manifeste](../../data/manifests/qwen3-1.7b-base-kaggle-private-v1.json).

## Ce qui a été fait

Le modèle de base épinglé a été enregistré une fois comme dataset Kaggle privé avec ses
poids, son tokenizer, ses configurations, sa licence déclarée et un manifeste par fichier.
Les futurs notebooks attachent cette ressource et chargent vLLM depuis `/kaggle/input`.

## Pourquoi le checksum porte sur tout le snapshot

Vérifier uniquement le nom du modèle ne garantit ni les poids, ni le tokenizer, ni la
configuration. Vérifier uniquement le gros fichier ne protège pas contre un tokenizer ou un
`config.json` différent. Le manifeste épinglé sert donc de racine de confiance et chaque
fichier est ensuite rehashé avant l'installation coûteuse des dépendances.

## Pourquoi le tokenizer SFT reste utilisé pour l'inférence

Le snapshot conserve le tokenizer source exact, mais le service historique utilise le
tokenizer archivé avec le SFT et son template de conversation. Changer ce tokenizer en même
temps que la source des poids rendrait la comparaison impossible à interpréter. Le cache des
poids est donc optimisé maintenant ; le comportement de tokenisation reste constant.

## À retenir

- une révision Git épinglée et un checksum de fichier répondent à deux risques différents ;
- une ressource privée attachée évite un téléchargement externe sans rendre le modèle public ;
- le préflight doit précéder l'installation et le chargement GPU ;
- poids, tokenizer, dépendances Python et image CUDA sont quatre couches de cache distinctes ;
- la prochaine économie porte sur l'environnement vLLM, pas sur un nouvel entraînement.
