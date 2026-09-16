# Évaluation de développement du parcours de triage — v23

- Date : 2026-09-12
- Statut : draft — v23 terminée en erreur au contrôle de recharge
- Environnement : Kaggle privé `pierrepluton/chsa-source-sft-qwen3`, T4 gratuite, même image et versions ML que v22 ; FastAPI 0.141.1 et ijson 3.5.1 pour les contrats locaux.
- Sources : [mission auditée](AUDIT_ALIGNEMENT_MISSION_2026-09-12.md), [protocole proposé](../../configs/educational_triage_protocol_v1.json), [scénarios](../../data/samples/synthetic-triage-development-v2.json), [identité SFT](../../configs/sft-v22-handoff.json).

## Question

Comment le modèle Base et le SFT général à 500 étapes répondent-ils à des situations de triage synthétiques, avec les mêmes consignes et le même contrat de sortie ? Cette expérience complète la comparaison QA. Elle ne mesure pas une performance clinique et ne remplace pas la validation vLLM/API.

## Protocole figé au lancement

- 18 scénarios de développement : neuf familles, chacune en français et anglais.
- Références dérivées du protocole éducatif existant, statut `proposed_educational_only`. Elles ne figurent pas dans les prompts.
- Modèle Base puis adaptateur général v22 ; aucun poids de mémorisation et zéro étape d'optimisation.
- Même tokenizer, prompt, schéma, greedy et plafond de 512 tokens ; maximum observé de 470 tokens pour les prompts locaux.
- Sorties brutes conservées ; schéma JSON vérifié strictement, sans extraire/réparer une réponse invalide. Aucun décodage contraint, aucun garde-fou API appliqué.
- Accord avec les références sur tous les cas, en comptant les sorties invalides comme non concordantes ; métriques sur sorties valides explicitement séparées.
- Nombre de questions complémentaires et d'informations manquantes : mesures de présence uniquement. La pertinence des questions, les recommandations dangereuses et l'adaptation au fil d'un échange nécessitent une revue et des essais supplémentaires.
- Avant la partie SFT, recharge vérifiée sur les 30 générations QA v22, comparaison des tokens exacte. Une différence arrête l'expérience et doit être diagnostiquée ; l'archive est préservée avant l'inférence.
- Les 500 exemples de test SFT ne sont pas utilisés.

## Correction de la référence de démonstration

Le jeu historique `synthetic-triage-evaluation-v1.json` attendait `deferred` pour informations insuffisantes et contradictoires. Le protocole adopté ultérieurement prévoit `moderate` dans ces situations. La v2 de développement applique ce protocole ; la v1 est conservée comme trace historique, et ses scores ne doivent pas être comparés directement à la v2. Aucun nouveau seuil clinique n'a été inventé.

## Vérification et lancement

Sept tests ciblés triage/DPO passent avant lancement, Ruff passe, le bootstrap est compilable et les dix-huit prompts respectent le budget. La vérification complémentaire des contrats API/serving porte le total à **16 tests passants**, avec une dépréciation Starlette/httpx sans échec. Ce sont des preuves locales de préparation et de contrats, pas des résultats du modèle.

```sh
PYTHONPATH=src python scripts/build_kaggle_triage_probe.py \
  --output artifacts/kaggle/triage-v23-launch \
  --metadata artifacts/kaggle/continuation-v22-launch/kernel-metadata.json
kaggle kernels push -p artifacts/kaggle/triage-v23-launch
kaggle kernels status pierrepluton/chsa-source-sft-qwen3
```

La CLI a confirmé la version 23 puis `RUNNING`. Notebook : 29 645 octets ; SHA-256 `b48ce9011d1473058d1efbf20353d17aecd2aad0cc722d41c3afb751b5d1d5d1`. Résumé v22 attendu : `45d6c88ef5e17e150a38f5ca7593212619ff854febe10901635f98913a6edb75`.

Les artefacts de sortie attendus sont `triage-base-sft-v23/base.json`, `sft.json`, `reload.json` et `summary.json`. Aucun résultat GPU n'est encore affirmé dans cette note de lancement.

## Résultat terminal et diagnostic du 12 septembre

La version Kaggle 23 (`scriptVersionId=349313211`) a terminé en erreur :
`ValueError: Reload generations differ; inspect runtime before interpreting results`.
Les sorties Base sont présentes ; la génération de triage SFT et le résumé comparatif
n'ont pas été exécutés. Le contrôle retrouve 14/30 séquences identiques : les quinze
réponses EN et une FR diffèrent. Il n'enregistrait que les booléens, ce qui empêche
de localiser les divergences. SHA-256 du `reload.json` téléchargé :
`70710bf2fd26995c79f229c5b2ec4f6fb3e5523e4a0bc75f0b1a6229c539b4a2`.

Les logs signalent explicitement l'import tardif d'Unsloth après Transformers/PEFT.
Le script d'entraînement importe au contraire Unsloth en premier. Le script
comparatif rétablit désormais cet ordre. Cette divergence est établie ; son rôle
causal dans les différences de génération n'est pas encore prouvé.

La prochaine exécution ne change ni données, ni poids, ni consignes, ni génération.
Elle teste cet ordre d'import et sauvegarde après chaque QA les tokens attendus,
observés et la première différence. Le contrôle d'arrêt reste strict. Le test local
couvre différences de tokens, troncature et égalité (trois tests du module passants,
Ruff passant). Cela valide le diagnostic local, pas la recharge GPU.
