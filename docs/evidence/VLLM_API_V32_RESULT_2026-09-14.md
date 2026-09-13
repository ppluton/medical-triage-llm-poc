# Résultat v32 : intégration GPU vLLM et API

Date : 2026-09-14 — Statut : draft
Sources : manifeste compagnon `VLLM_API_V32_RESULT_2026-09-14.json`, artefacts privés v32 (349509492), code 37c80f1.

## Protocole et résultat

Deux adaptateurs sauvegardés SFT 500 et DPO v27, même base et tokenizer archivés, vLLM 0.15.0 en FP16, schéma JSON contraint, T4, 18 scénarios synthétiques de développement par variante. Aucun entraînement ni test réservé. La CLI a confirmé COMPLETE. Les sorties sont récupérées sous `artifacts/kaggle/vllm-api-v32-reports/vllm-api-v32` avec `kaggle kernels output pierrepluton/chsa-source-sft-qwen3/32` et filtre de ce répertoire.

| Mesure | SFT | DPO |
|---|---:|---:|
| Réponses API conformes | 12/18 | 12/18 |
| Priorités correspondant aux références proposées | 6/18 | 5/18 |
| Cas critiques avec réponse valide maximum | 4/6 | 4/6 |
| Erreurs HTTP 502 | 6/18 | 6/18 |
| Audit rapproché des réponses réussies | 12/12 | 12/12 |
| Latence médiane client | 21,878 s | 10,897 s |
| Latence p95 client | 42,709 s | 33,610 s |

Les références sont proposées à titre pédagogique, sans validation clinique. Les erreurs restent dans le dénominateur. Les priorités ont été recalculées en joignant les identifiants du fichier de scénarios aux réponses sauvegardées. Les latences incluent les échecs, en série. SFT passe avant DPO dans le même serveur : caches et échauffement empêchent d’attribuer l’écart de temps au seul DPO.

## Analyse des erreurs et limites

Le journal vLLM contient 36 réponses HTTP 200 à `/v1/chat/completions`. Les deux lots API échouent sur les mêmes six scénarios, listés dans le manifeste compagnon. Les journaux API ne détaillent pas la cause ; le code transforme les exceptions fournisseur et schéma en un même 502. Les métadonnées de terminaison et les sorties rejetées n’ont pas été conservées. Impossible de départager troncature, validation du schéma et anonymisation à partir de ces seules traces.

Des réponses valides restent répétitives. Le cas respiratoire anglais reçoit moderate au lieu du maximum proposé ; les contextes pédiatrique et de vulnérabilité anglais reçoivent deferred au lieu de moderate. Aucun gain de triage DPO n’est démontré. Le format contraint ne garantit pas la pertinence du contenu.

La liaison CUDA et l’intégration réelle sont désormais prouvées pour ce run. Ni persistance après redémarrage, ni disponibilité extérieure, ni charge concurrente, ni validation clinique ne sont prouvées. Les poids n’ont pas été réentraînés.

## Suite

Ajouter une classification technique bornée des erreurs, sans texte patient ni détail d’exception, puis reproduire les requêtes en échec. Conserver les contrôles existants : ne pas accepter une réponse incomplète pour améliorer artificiellement le taux de réussite. Terminer ensuite évaluation réservée, déploiement autorisé et rapport.

## Classification ajoutée après le run

Le fournisseur classe désormais les exceptions avec huit codes techniques bornés. L’API ajoute uniquement `failure_code` aux traces d’échec ; le message public 502 reste générique. Aucun corps rejeté ni message brut d’exception n’est persisté. Cette instrumentation ne permet pas de reconstituer rétroactivement la cause des erreurs v32.

Validation : `PYTHONPATH=src python -m pytest tests/test_serving.py -q` : 12 tests réussis ; Ruff sur les deux modules et le fichier de tests : succès. Les tests vérifient le rejet des sorties tronquées/invalides et l’absence du contenu privé dans réponse et audit. Nouvelle exécution GPU nécessaire pour classer les échecs réels.
