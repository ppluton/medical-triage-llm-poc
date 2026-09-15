# Lancement de l’évaluation finale QA v35

Date : 2026-09-14 — Statut : draft
Sources : configs/final-evaluation-frozen-v1.json, manifeste compagnon FINAL_QA_V35_LAUNCH.json, paquet local final-qa-v35-package.

Le test réservé a été exporté depuis le corpus canonique vérifié : 500 exemples, SHA-256 103f5bcb522073fe385c656c9dc0071c5cd91d803b97a77a5f65e710a88e1dce. Cinquante identifiants de génération sont sélectionnés par hash avec seed 42, sans choix à partir des réponses. Le gel vérifie données, manifestes, checkpoint via son manifeste, résumé DPO, runner, sélection et terminaison, ainsi que quatre versions de packages.

Le paquet dérive du builder de comparaison existant : les entrées de développement ont été retirées du contenu embarqué et remplacées par test, manifeste et gel. La commande utilise exclusivement `--test` et `--final-freeze` ; la sortie est `/kaggle/working/final-qa-v35`. Le bootstrap installe explicitement Torch 2.10.0 depuis l’index officiel CUDA 12.8 avant les dépendances communes. Le runner refuse un écart aux versions figées.

Contrôles avant lancement : compilation du bootstrap, validation des empreintes figées, 500 enregistrements et 50 identifiants déterministes. Push privé accepté comme version 35, statut RUNNING confirmé. Aucun résultat n’est encore établi.

L’objectif est une comparaison QA indépendante Base/SFT/DPO en Transformers FP4 avec génération libre de 512 tokens. Elle ne mesure pas l’API vLLM FP16 à sorties contraintes. Les résultats de ce test ne serviront pas à régler les modèles. Les contrôles du parcours de triage, la démonstration extérieure et le rapport final restent distincts.

## Observation du journal — 14 septembre

Le [journal privé v35](https://www.kaggle.com/code/pierrepluton/chsa-source-sft-qwen3?scriptVersionId=349810521) affiche une exécution active après environ 27 minutes. La Base atteint 500 exemples de loss à 351,7 secondes ; le SFT atteint 500 à 1 317 secondes. Aucun jalon DPO n'est encore visible. L'ordre du runner situe ensuite le calcul dans les générations SFT ; le journal ne donne pas leur compteur intermédiaire. Les valeurs de loss et la qualité finale ne sont pas encore vérifiées. Aucun relancement n'est justifié par cette observation.
