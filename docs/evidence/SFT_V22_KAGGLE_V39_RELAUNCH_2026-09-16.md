# Relance SFT v2.2 — Kaggle v39

- Date : 2026-09-16
- Statut observé : `RUNNING`
- Notebook privé : `pierrepluton/chsa-source-sft-qwen3`, version 39
- Révision de correction : `9258fe4`
- Notebook SHA-256 : `3772c9c49e88645803a6586049aafaa4dd1c03e0c21bd53b2db96d035c790520`
- Statut clinique : aucune validation clinique

## Correction ciblée

La v38 a prouvé le snapshot Qwen complet puis a échoué avant entraînement parce que son
tokenizer Base exact ne contient pas de chat template. La v39 conserve ce tokenizer et
ajoute le template de conversation dans un fichier versionné séparé :
`configs/qwen3-source-sft-chat-template.jinja`, SHA-256
`b44d8063c3b49558db444116213856583a953510918d3eac9c58bf1b35c905b0`.

Un test local compare son rendu au template audité historique sur les messages système,
utilisateur et assistant du projet. Le runner vérifie le checksum avant de l'affecter au
tokenizer ; les poids et le vocabulaire du snapshot restent inchangés.

## Périmètre inchangé

La v39 utilise exactement les mêmes hashes train/validation, le même snapshot Base, la même
seed et les mêmes hyperparamètres bornés que v38. Aucun test n'est embarqué. Le statut
`RUNNING` prouve la relance seulement ; smoke, reprise, 150 étapes et résultats restent à
observer.
