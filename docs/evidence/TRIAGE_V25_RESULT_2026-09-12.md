# Comparaison de triage v25 et correction de recharge

- Date : 2026-09-12
- Statut : draft — résultats techniques observés, validation clinique non effectuée
- Sources : [mesures et empreintes](TRIAGE_V25_RESULT_2026-09-12.json), [protocole proposé](../../configs/educational_triage_protocol_v1.json).

## Exécution et question

Notebook privé `pierrepluton/chsa-source-sft-qwen3`, version 25, scriptVersionId
349322069, terminé sur Kaggle T4 gratuit. Base Qwen3-1.7B-Base figée et SFT général
500 étapes identifié par `configs/sft-v22-handoff.json`. Aucune étape d'optimisation,
aucun exemple du test final utilisé. Dix-huit scénarios synthétiques de développement,
neuf familles en français et anglais, génération brute plafonnée à 512 tokens.

Récupération : `kaggle kernels output pierrepluton/chsa-source-sft-qwen3/25 -p artifacts/kaggle/triage-v25-reports --page-size 200 --file-pattern '.*(triage-base-sft-v25/.*\.json|\.log)$'`.
Les sorties brutes restent hors Git ; leurs empreintes figurent dans le JSON associé.
Le calcul local avec `score_outputs` reproduit les agrégats GPU.

## Résultats

Le chargement des poids SFT était exact, mais 392 copies de tenseurs du cache
Unsloth conservaient les anciennes valeurs après l'inférence Base. La transition
`for_training` puis `for_inference` vide ce cache. Les trente générations QA de
contrôle deviennent identiques token par token à la sauvegarde SFT 500. Cela
établit la fidélité de recharge dans ce runtime, pas la qualité des réponses.

| Mesure | Base | SFT 500 |
|---|---:|---:|
| JSON conforme | 0/18 | 10/18 |
| Priorité conforme à la référence proposée, tous les cas | 0/18 | 4/18 |
| Arrêt EOS | 4/18 | 10/18 |
| Plafond 512 tokens | 14/18 | 8/18 |
| Sortie valide et maximum correct, tous les cas critiques | 0/6 | 2/6 |

Le rappel de 100 % calculé uniquement sur les sorties valides du SFT exclut quatre
cas critiques invalides : il ne doit pas être présenté comme le résultat global.
Des faits inventés et des priorités insuffisantes sont observés. Les résultats ne
constituent pas une validation clinique ni une preuve d'aptitude au triage.

## Limite du protocole et prochaine étape

La consigne v25 ne donnait pas explicitement les définitions des trois priorités
utilisées par les références proposées. Elle ne constitue donc pas le protocole
final. La prochaine comparaison doit expliciter ces définitions de façon identique
pour tous les modèles, garder les références hors du prompt et conserver v25 comme
résultat historique. Aucun nouveau SFT long n'est justifié par cette seule mesure.
