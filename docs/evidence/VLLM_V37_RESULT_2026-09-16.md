# Résultat v37 — API 0.4.0 et garde-fous

- Date : 2026-09-16
- Statut : terminé avec un échec Base `generation_length`
- Résultat compact : [JSON compagnon](VLLM_V37_RESULT_2026-09-16.json)
- Run : version 37 du notebook Kaggle privé `pierrepluton/chsa-source-sft-qwen3`
- Données : 18 scénarios synthétiques de développement, aucun test final
- Entraînement : aucun ; Base, SFT et DPO existants inchangés
- Statut clinique : aucune validation clinique.

## Résultats automatiques

| Mesure | Base | SFT | DPO |
|---|---:|---:|---:|
| Réponses réussies | 17/18 | 18/18 | 18/18 |
| Accord de priorité proposé, échecs inclus | 16/18 | 15/18 | 15/18 |
| Rappel critique proposé | 6/6 | 6/6 | 6/6 |
| Critiques avec `red_flags` | 6/6 | 6/6 | 6/6 |
| Plancher de priorité sur l'incertitude | 3/4 | 4/4 | 4/4 |
| Sortie modèle conservée | 4 | 5 | 4 |
| Sortie corrigée | 8 | 5 | 5 |
| Remplacement conservateur | 5 | 8 | 9 |

La Base échoue sur le scénario contradictoire anglais : la génération atteint la limite et
l'API retourne correctement 502 au lieu de livrer une réponse incomplète. L'audit enregistre
`failure_code=generation_length`. Les 53 réponses endpoint réussies et les 36 réponses de
collecte sont rapprochées de leur audit ; toutes les synthèses de garde-fous portent la
version attendue.

## Interprétation

Les garde-fous corrigent les régressions critiques visibles en v36 : les trois variantes ont
6/6 priorités critiques proposées et 6/6 couvertures `red_flags` sur les réponses obtenues.
SFT et DPO imposent le plancher proposé sur les quatre cas d'incertitude.

En revanche, ils interviennent sur la majorité des réponses : seulement 4 à 5 sorties sur 18
sont conservées telles quelles et 8 sorties SFT / 9 sorties DPO sont entièrement remplacées.
La chaîne contient donc mieux les signatures connues, mais le modèle n'est pas devenu fiable
par lui-même. Aucun bénéfice DPO par rapport au SFT n'est démontré : leurs métriques
automatiques sont identiques, avec un fallback DPO supplémentaire.

## Ce qui est prouvé

- le vrai runtime FP16 Base/SFT/DPO exécute l'API 0.4.0 et les garde-fous versionnés ;
- les réponses réussies, leurs audits et les décisions de garde-fou se rapprochent ;
- les trois parcours de collecte terminent 12 appels et leurs audits passent ;
- une génération incomplète est refusée au lieu d'être transformée en succès ;
- aucune étape d'entraînement ni aucun exemple du test final n'est utilisé.

## Ce qui reste ouvert

Le lot est déjà vu et les sorties finales n'ont pas encore reçu une nouvelle revue aveugle
qualitative. Les métriques ne prouvent ni l'absence de formulations inventées non détectées,
ni la pertinence clinique des règles. Le run reste privé et local à Kaggle : il ne satisfait
pas l'exigence d'un endpoint cloud accessible de l'extérieur.

La prochaine régression v38 utilisera la même chaîne et les mêmes poids, mais chargera le
modèle de base depuis la nouvelle ressource Kaggle privée afin de supprimer le téléchargement
Hugging Face récurrent. Elle ne doit être lancée que pour valider ce changement d'infrastructure,
pas pour chercher un score différent.
