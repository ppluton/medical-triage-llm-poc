# Ressource Kaggle privée Qwen3-1.7B-Base

- Date : 2026-09-16
- Statut : ressource privée prête ; rehash distant au premier runtime attaché
- Manifeste : [qwen3-1.7b-base-kaggle-private-v1.json](../../data/manifests/qwen3-1.7b-base-kaggle-private-v1.json)
- Cible : `pierrepluton/qwen3-1-7b-base-e249956c`, dataset Kaggle privé 12040702
- Usage : cache reproductible du modèle de base pour le POC éducatif.

## Vérifications avant envoi

Le snapshot Hugging Face local est exactement la révision
`e249956c10337100486d07afb77e3eb2b30906b8`. Le model card identifie
`Qwen/Qwen3-1.7B-Base` comme base et déclare la licence Apache-2.0. La page source épinglée
affiche la même révision et la même licence.

Les onze fichiers source ont été hachés avant l'envoi. Le poids
`model.safetensors` mesure 3 441 185 608 octets et porte le SHA-256
`6df85b39330e5a425ee36253d0f894e4387e4f0a15b9c53cb467d668e6b3a841`, identique au
hash LFS du cache Hugging Face. Le tokenizer exact et ses configurations sont inclus.

Le constructeur refuse une révision différente, une licence autre qu'Apache-2.0, un fichier
manquant ou un checksum modèle différent avant de créer le dossier d'upload.

## Vérifications après envoi

Kaggle indique `ready`, `isPrivate=true`, la licence `apache-2.0` et les douze fichiers
attendus : les onze fichiers source plus `MODEL_SNAPSHOT_MANIFEST.json`. Les tailles
distantes du modèle et du tokenizer correspondent au manifeste. Le manifeste redescendu
depuis Kaggle porte le même SHA-256 `920a5897…f0d1` que celui envoyé.

Le poids distant de 3,2 Gio n'a pas été redescendu une seconde fois uniquement pour le
rehacher. À la place, tout futur notebook exécute avant même l'installation de vLLM un
préflight qui vérifie le manifeste épinglé, la licence, la révision et les checksums des
onze fichiers. Le démarrage échoue fermé au premier écart.

## Raccord aux futurs notebooks

Le builder ajoute automatiquement `pierrepluton/qwen3-1-7b-base-e249956c` à
`dataset_sources`. Le runner reçoit `/kaggle/input/qwen3-1-7b-base-e249956c`, lance vLLM
depuis ce chemin local et n'utilise plus l'identifiant Hugging Face dans sa commande modèle.
Le candidat local `api-local-base-v38` contient 48 fichiers embarqués, zéro divergence avec
le checkout et exécute le préflight avant la création des environnements Python.
Son notebook porte le SHA-256 `46242e70…1dd3`. Les huit tests ciblés passent ; la
régression complète `val_c39659679a1b` passe 205 tests en 23,57 secondes avec le seul
avertissement externe Starlette/httpx déjà connu. Ruff passe sur l'ensemble du dépôt.

Le tokenizer SFT reste celui utilisé par vLLM afin de ne pas changer simultanément le rendu
de prompt et la source des poids. Le tokenizer original reste conservé avec les poids et
vérifié pour la provenance. Une éventuelle convergence de tokenizer sera une expérience
distincte.

## Limite suivante

Cette brique retire le téléchargement Hugging Face récurrent du modèle. Elle ne retire pas
l'installation répétée de `vllm==0.15.0`, de l'environnement API et des modèles spaCy. La
prochaine optimisation doit figer un environnement ou une image compatible Kaggle/CUDA,
avec ses propres checksums et un fallback documenté.
