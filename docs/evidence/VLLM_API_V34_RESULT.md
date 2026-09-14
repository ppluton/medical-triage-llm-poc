# Résultat v34 : réponses complètes et limites de triage

Date : 2026-09-14 — Statut : draft
Sources : manifeste compagnon VLLM_API_V34_RESULT.json, run privé Kaggle v34, code c096755 et builder d3417ca.

## Mesure

CLI COMPLETE, 18 scénarios synthétiques de développement par adaptateur, mêmes poids SFT 500 et DPO v27. Prompt v4, listes de deux éléments maximum, résumé borné, budget 768 tokens, contexte vLLM 4096, FP16. Aucun entraînement ni test réservé.

| Mesure | SFT | DPO |
|---|---:|---:|
| Réponses conformes | 18/18 | 18/18 |
| Erreurs | 0/18 | 0/18 |
| Priorités correspondant aux références proposées | 8/18 | 8/18 |
| Six scénarios critiques proposés classés maximum | 6/6 | 6/6 |
| Audit rapproché des réponses | 18/18 | 18/18 |
| Latence client médiane | 7,719 s | 7,178 s |
| Latence client p95 | 38,323 s | 22,011 s |

Les priorités ont été recalculées par jointure des identifiants avec le fichier de scénarios. Les trois changements de génération ont été appliqués ensemble ; leur effet individuel n’est pas isolé. La mesure est séquentielle, SFT avant DPO : caches et échauffement interdisent une conclusion causale sur la vitesse du DPO.

## Limites observées

Les deux variantes proposent les mêmes priorités : maximum ou deferred, jamais moderate. Les dix scénarios attendus moderate sont donc tous discordants. Les cas anglais pédiatrique, de vulnérabilité et d’informations insuffisantes sont classés deferred. Plusieurs cas français sont au contraire classés maximum. Ces différences de langue et l’absence du niveau intermédiaire empêchent de déclarer le parcours de triage satisfaisant. Les questions complémentaires sont absentes sur les scénarios d’informations insuffisantes.

Le correctif résout les rejets observés sur ce lot, mais n’établit pas la pertinence clinique. Les références sont proposées à titre pédagogique et le lot a servi au développement. Aucun gain de triage DPO démontré. Aucun accès extérieur ni persistance après redémarrage prouvés.

## Suite

Conserver cette configuration comme base technique de démonstration et ses limites explicites. Vérifier les garde-fous pour informations insuffisantes et le parcours de questions complémentaires, puis effectuer l’évaluation finale isolée. Le déploiement sur cible autorisée et le rapport final restent à terminer.
