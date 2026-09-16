# Résultat final de la réserve sélectionnée — v46

- Date : 2026-09-16
- Statut : `completed_negative_result_not_clinical_validation`
- Notebook privé : `pierrepluton/chsa-source-sft-qwen3`, version 46
- Candidat évalué : SFT v39, étape 150
- Manifeste : `data/manifests/selected-reserve-v46-result-v1.json`
- Optimisation : 0 étape
- Réserve : 18/18 scénarios, une seule variante

## Intégrité

Le run vérifie avant chargement onze fichiers du snapshot Base, sa révision, sa licence et son
manifeste. Il recharge le SFT sélectionné par la décision v43. DPO n’est ni monté ni chargé.
Le résumé confirme 18 cas de réserve, zéro exemple de développement, zéro test QA et zéro
étape d’optimisation. Le vérificateur local recalcule le score depuis les 18 sorties dans le
même ordre et retrouve exactement les métriques sauvegardées.

## Résultat automatique

| Mesure | Résultat |
|---|---:|
| JSON conformes | 0 / 18 |
| Accord aux niveaux proposés | 0 / 18 |
| Arrêts EOS | 1 / 18 |
| Générations au plafond 512 tokens | 17 / 18 |
| Répétition moyenne de 4-grammes | 0,8289 |
| Latence p50 séquentielle | 52,707 s |
| Latence p95 séquentielle | 53,591 s |

La seule génération qui s’arrête par EOS reproduit le contexte utilisateur au lieu du contrat
de sortie. Les dix-sept autres atteignent le plafond et répètent fortement du texte.

## Revue de projet des 18 sorties

Les dix-huit sorties sont signalées comme malformées ou répétitives. L’assistance bornée
signale également au moins six affirmations patient non étayées, deux formulations
diagnostiques/prescriptives et cinq priorités inférieures à `maximum` sur des scénarios proposés
critiques. La lecture intégrale confirme notamment des âges, antécédents, médicaments,
constantes normales et symptômes inventés.

Ces détections lexicales sont des minima techniques, pas une estimation clinique du risque.
Elles peuvent manquer d’autres erreurs ou signaler un mot médical utilisé dans un contexte
informatif.

## Conclusion de l’étape modèle

Le SFT v39 apprend mieux les réponses QA du corpus et se recharge de façon reproductible, mais
il n’est pas capable de produire seul une sortie de triage fiable sur la réserve. Le DPO v41
n’a pas été retenu car ses gains de forme ne dominaient pas le SFT et sa revue de développement
ajoutait un flag diagnostic.

Le POC doit donc présenter le modèle comme un composant expérimental derrière un schéma
contraint, des garde-fous déterministes et une décision humaine obligatoire. Les résultats de
réserve sont finaux : ils ne seront utilisés pour modifier ni poids, ni prompt, ni garde-fous,
et le run ne sera pas répété.
