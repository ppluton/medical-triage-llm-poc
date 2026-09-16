# Lancement SFT v2.2 — Kaggle v38

- Date : 2026-09-16 à 03:40 Asia/Tbilisi
- Statut final : `ERROR` avant toute étape d'entraînement
- Notebook privé : `pierrepluton/chsa-source-sft-qwen3`, version 38
- Révision de code : `c2db5e491099d1c638d2e688bd4d669a1111b5de`
- Notebook SHA-256 : `23149fc0d4bb49866774119ffebe9a1031d58f0373cd9c5f140fba316796cf28`
- Statut clinique : aucune validation clinique

## Périmètre

Le run exécute le pilote LoRA borné sur le corpus final v2.2 : 3 721 lignes train,
479 validation et zéro ligne test. Il part de la ressource privée Qwen3-1.7B-Base à la
révision `e249956c10337100486d07afb77e3eb2b30906b8`, sans adaptateur historique.

Avant l'installation des dépendances, le premier code du notebook vérifie le manifeste,
la licence et les checksums de tous les fichiers du snapshot attaché. Le modèle et le
tokenizer sont ensuite chargés depuis `/kaggle/input/qwen3-1-7b-base-e249956c` ; aucun
téléchargement Hugging Face des poids n'est prévu.

## Bornes

- arrêt à 150 optimizer steps ou 1 800 secondes de phase entraînement ;
- checkpoints complets tous les 50 pas ;
- seed 42, LoRA rank 16, alpha 16, learning rate `1e-4` ;
- smoke GPU et reprise de checkpoint avant le pilote ;
- aucune continuation automatique ni DPO dans cette version.

## Niveau de preuve

Kaggle a accepté la version 38 et la CLI a d'abord observé `RUNNING`. Le log récupéré
prouve ensuite `BASE_SNAPSHOT_PREFLIGHT_PASSED 11`, puis un arrêt du smoke avant toute
étape : le tokenizer exact du modèle Base ne définit pas de chat template. L'erreur est
`Cannot use chat template functions because tokenizer.chat_template is not set`.

Le snapshot, les données et les checksums ne sont pas en cause. Aucun checkpoint v38 n'a
été produit et aucun poids n'a été modifié. La correction versionne séparément le template
de conversation et vérifie son hash avant le rendu ; elle est relancée en v39.
