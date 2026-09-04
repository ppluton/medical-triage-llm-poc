# Micro-run SFT source-derived avec Unsloth Core/MLX

- **Date :** 2026-09-04
- **Statut :** observed — technical micro-run completed
- **Code :** `33418fc`
- **Dataset :** `derived-source-medical-qa-sft-v1`
- **SHA-256 dataset :** `da7b7913cc70a4cd1c340d8afb1bfcc910af5eb7b8511f81b18f356d8420b347`
- **Sources :** configuration `source_sft_lora.yaml`, runner `run_source_sft_mlx.py`, résumé local du run

## Question

La chaîne Qwen3 Base, dataset SFT source-derived, LoRA et Unsloth Core/MLX peut-elle terminer un premier run contrôlé et sauvegarder un adaptateur sans utiliser le test ?

## Configuration observée

- modèle : `Qwen/Qwen3-1.7B-Base`, snapshot `e249956c10337100486d07afb77e3eb2b30906b8` ;
- quantification de la base : 4 bits MLX ;
- LoRA : rang 16, alpha 16, batch 1, accumulation 8 ;
- seed : 42 ;
- longueur maximale : 2 048 tokens ;
- étapes : 20 ;
- données disponibles : 4 000 train et 500 validation ;
- validation utilisée par le smoke test : 50 lignes déterministes, dont 29 MedQuAD, 15 MediQAl et 6 FrenchMedMCQA ;
- test utilisé : 0 ligne.

## Résultat

| Mesure | Valeur observée |
|---|---:|
| Étapes terminées | 20 |
| Tokens entraînés | 40 574 |
| Train loss | 2,5571 |
| Eval loss | 2,2279 |
| Eval perplexity | 9,2803 |
| Durée | 5 921,36 s, soit environ 98 min 41 s |
| Pic mémoire MLX | 3,117 Go |

L'adaptateur local `adapters.safetensors` pèse 69 772 950 octets et porte le SHA-256 `3584c68de4e1e06a41603f10b41cecd2f2240a95c2de67bfbbd087b339fc388c`. Le fichier reste hors Git dans `artifacts/unsloth-core-source-sft-micro-run/`.

## Ce que cela prouve

- les fichiers source-derived sont acceptés par le runner réel ;
- les trois sources apparaissent dans la validation du smoke test ;
- les 20 étapes se terminent sur Apple MLX ;
- un adaptateur et son template sont sauvegardés ;
- le split test demeure exclu.

## Ce que cela ne prouve pas

- la convergence sur les 4 000 exemples ;
- une amélioration par rapport au modèle Base ;
- une capacité fiable à produire les trois niveaux de triage ;
- la sûreté ou la pertinence clinique.

Les losses de ce micro-run ne doivent pas être comparées directement à celles du micro-run synthétique précédent : données, longueurs et validation diffèrent.

## Étape suivante

Estimer la durée et le nombre d'époques du run complet, fixer une stratégie de sauvegarde et d'arrêt, exécuter toute la validation, puis comparer Base et SFT sur le même protocole isolé.
