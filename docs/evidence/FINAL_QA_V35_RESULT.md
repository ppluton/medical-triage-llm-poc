# Comparaison finale QA — Base, SFT et DPO

Date : 2026-09-16 — Statut : draft
Sources : run Kaggle privé v35 (scriptVersionId 349810521), protocole `configs/final-evaluation-frozen-v1.json`, manifeste compagnon `FINAL_QA_V35_RESULT.json`.

## Protocole et vérification

500 exemples de test isolés ; 50 prompts choisis par hash et seed 42, identiques pour les trois modèles. Base Qwen3-1.7B, SFT 500 étapes, DPO v27 20 étapes. Transformers 4.57.6, PEFT 0.18.1, Torch 2.10.0+cu128, bitsandbytes 0.50.2 ; FP4, génération greedy, plafond de 512 tokens, zéro étape d'optimisation.

Kaggle indique COMPLETE. Les six fichiers ont été téléchargés et `scripts/verify_final_comparison.py` recalcule les métriques. Le contrôle vérifie populations, ordre des identifiants, sélection, versions, empreintes des manifestes, code du runner et gel enregistré. Les empreintes des résultats sont consignées dans le manifeste compagnon. Aucun paramètre n'est ajusté à partir de ces résultats.

Commande exécutée :

```sh
PYTHONPATH=src python scripts/verify_final_comparison.py \
  --run artifacts/kaggle/final-qa-v35-reports/final-qa-v35 \
  --test artifacts/final-evaluation-v1/test-qwen3.jsonl \
  --freeze configs/final-evaluation-frozen-v1.json \
  --output artifacts/kaggle/final-qa-v35-reports/verified-result.json
```

## Mesures

| Mesure | Base | SFT | DPO |
|---|---:|---:|---:|
| Perte réponse moyenne par exemple, 500 tests | 1,575202 | 0,844017 | 0,842970 |
| Arrêts EOS déclarés, sur 50 générations | 37 | 40 | 41 |
| Sans arrêt EOS déclaré, sur 50 | 13 | 10 | 9 |

43 des 50 sorties SFT et DPO sont identiques caractère pour caractère. Ce constat descriptif complémentaire ne constitue pas un test de significativité.

Le SFT réduit la perte de réponse sur le corpus réservé. L'écart DPO/SFT est faible sur cette métrique ; l'essai ne démontre pas un bénéfice général du DPO. La perte mesure la probabilité des réponses de référence, pas leur justesse clinique. Les sorties nécessitent encore une analyse qualitative ; un arrêt EOS ne suffit pas à établir la qualité du texte.

## Limites et suite

Les observations sauvegardées sont vérifiées sans rejouer l'inférence. Les drapeaux EOS sont contrôlés et recomptés, mais pas recalculés avec le tokenizer. Il ne s'agit pas d'une évaluation clinique ni du parcours API contraint vLLM FP16. Aucun gain de triage ne peut être déduit de ces chiffres.

La comparaison API v36 utilise uniquement les scénarios synthétiques de développement, avec le même prompt pour Base/SFT/DPO et le nouveau suivi de collecte. Elle est distincte de ce test final QA. Ses résultats restent à récupérer ; l'endpoint extérieur, la CI/CD de déploiement et les livrables finaux restent à achever.
