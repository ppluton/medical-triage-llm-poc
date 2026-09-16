# Vérification avant le pilote SFT v2 — 11 septembre 2026

- Date : 2026-09-11
- Statut : draft — contrôles techniques locaux réussis, pilote GPU non lancé
- Sources : cadrage, spécification, ADR-008/012, manifestes v2/v2.1/revu, rapports JSON liés ci-dessous.
- Périmètre : qualité de transformation, isolation des données, labels réels du trainer et sauvegarde/reprise. Aucun jugement clinique ni entraînement du modèle médical.

## Verdict

Le candidat retenu pour préparer le pilote est **`derived-source-medical-qa-sft-v2.1-reviewed`**, soit **4 700 lignes : 3 721 train, 479 validation, 500 test**. « v2.1 » désigne une révision de données, pas un entraînement supplémentaire. Le corpus v2 historique et ses résultats restent conservés.

Le candidat passe les contrôles techniques définis ici. Cela ne certifie pas que chaque affirmation médicale est exacte, actuelle, sans paraphrase ailleurs, ou que l'entraînement améliorera le modèle. Les questions-réponses n'ont pas reçu de validation clinique.

## Défauts supplémentaires constatés et traitement

L'audit v2 initial comptabilise 145 documents MedQuAD présents dans plusieurs splits. En étendant les groupes aux questions sources identiques, aux vignettes communes et aux réponses MedQuAD identiques, **169 clés de groupes** traversent les splits. Une fermeture transitive permet d'exclure **276 lignes train et 21 validations**. Aucune ligne n'est déplacée d'un split à un autre ; les 500 tests restent strictement identiques.

La revue complémentaire identifie **3 QCM train avec choix dupliqués dans les sources**. Ils sont mis à l'écart, sans inventer une correction de la référence. La liste motivée est dans [les exclusions de revue](SFT_V2_SOURCE_REVIEW_EXCLUSIONS.json). Le filtrage final exclut donc 300 lignes du corpus v2.

L'isolation par document et empreinte est conservatrice. Elle ne constitue pas une recherche exhaustive de paraphrases. Les checkpoints SFT v5/v15–v17 ont été entraînés avant cette isolation : ils restent des références historiques, pas des concurrents offrant la même indépendance du test que le futur SFT depuis la base.

## Preuves directes

| Contrôle | Observation | Niveau et limite |
|---|---|---|
| Sources locales | Révisions MedQuAD et MediQAl épinglées, fichiers suivis inchangés ; archive FrenchMedMCQA conforme au hash | Prouvé localement ; licences/provenance consignées, pas une validation juridique |
| FrenchMedMCQA reconstruit | 2 191 lignes train reconstruites identiques aux lignes de l'archive | Splits reconstruits propres au projet ; ne pas présenter ce jeu comme le test original du benchmark |
| Fidélité des données finales | 4 195 rendus identiques aux sources + 5 différences reproduites exactement par l'anonymisation | Prouvé sur les 4 200 exemples de développement, dont 2 224 QCM |
| Identifiants directs | 8 400 champs rescannés, zéro signal résiduel dans la politique configurée | PERSON/LOCATION/DATE ne font pas partie de cette politique ; pas une certification d'anonymisation complète |
| Isolation | Zéro groupe défini traversant les splits ; test inchangé | Les empreintes de test servent à l'isolation, aucune génération ni revue des réponses test |
| Tokens | 4 200 frontières exactes, EOS unique, aucune troncature ; maximum 1 072 tokens train / 939 validation pour un contexte de 2 048 | Prouvé avec le tokenizer figé |
| Collateur TRL réel | 4 200 prompts masqués, toutes les réponses supervisées, EOS compris | Prouvé en CPU avec TRL 0.23.1 / Transformers 5.5.0 |
| Reprise d'entraînement | Modèle miniature synthétique : 4 étapes continues = 2 étapes + sauvegarde + reprise jusqu'à 4, poids LoRA identiques bit à bit | Prouvé sur CPU ; CUDA/Unsloth/quantification/scaler fp16 restent à vérifier |
| Régressions locales | 113 tests passent, Ruff et diff check passent | Tests de logique, contrats et API ; aucune preuve clinique |

Rapports : [audit des groupes](SFT_V2_GROUP_AUDIT_2026-09-11.json), [audit final](SFT_V2_READINESS_FINAL_2026-09-11.json), [trainer et reprise CPU](SFT_TRAINER_CONTRACT_CPU_2026-09-11.json), [provenance](SFT_V2_SOURCE_PROVENANCE_RECHECK.json).

## Environnement et reproductibilité

Worktree `codex/complete-poc-evaluation`, base de cette étape `d5bbbe2`. Les sorties brutes sont locales, hors Git. Les scripts et les rapports portent leurs SHA-256. Le runtime CPU utilise PyTorch 2.13.0 et les mêmes versions Transformers 5.5.0, TRL 0.23.1, PEFT 0.18.1, datasets 4.3.0 et accelerate 1.14.0 que le contrat préparé. Il n'émule pas la GPU T4.

Jobs `codex-validate` : audit final `val_22d167edcb8f`, trainer CPU final `val_65e642c05bf6`, suite `val_39f675162f77` (113 tests, 4,58 s ; une dépréciation Starlette/httpx). Le premier test synthétique de reprise signalait une frontière de token due à un espace terminal de la fixture ; la fixture finale utilise le même rendu contrôlé et le test a été répété sans cette ambiguïté.

```sh
PYTHONPATH=src python scripts/audit_sft_v2_readiness.py \
  --manifest data/manifests/derived-source-medical-qa-sft-v2.1-reviewed.json \
  --artifacts data/processed/source-sft-v2.1-reviewed \
  --original-tokenizer /path/to/frozen-tokenizer \
  --medquad /path/to/pinned-medquad --mediqal /path/to/pinned-mediqal \
  --french /path/to/frenchmedmcqa-rebuilt \
  --output /path/to/fresh-audit --scan-direct-identifiers

PYTHONPATH=src python scripts/verify_trainer_contract_cpu.py \
  --tokenizer /path/to/frozen-tokenizer \
  --data data/processed/source-sft-v2.1-reviewed --output /path/to/fresh-cpu-proof

PYTHONPATH=src python scripts/run_source_sft_pilot.py \
  --config configs/sft-v2.1-pilot.json --data data/processed/source-sft-v2.1-reviewed \
  --tokenizer /path/to/frozen-tokenizer --output /path/to/fresh-pilot
```

La dernière commande est un **préflight sans entraînement**. Le paramètre séparé d'exécution n'a pas été utilisé. Le validateur historique continue de refuser les manifestes candidats pour l'entraînement par défaut ; l'option d'audit ne leur accorde pas d'approbation.

## Prochain pilote préparé, non exécuté

Le [protocole](../../configs/sft-v2.1-pilot.json) repart de la base Qwen3-1.7B épinglée, avec LoRA neuf, et tire les batches du corpus train complet figé. Il s'arrête à **150 étapes ou 1 800 secondes**, au premier contrôle de fin d'étape concerné. Installation, compilation et évaluations ont un temps supplémentaire ; ce n'est pas une promesse de durée totale du notebook. Le budget inclut les pauses d'évaluation pendant `train()`.

La base et la fin du pilote sont comparées sur 479 losses de réponse et 30 générations fixes (15 EN, 15 FR), hors des trois diagnostics précédents. La loss est également évaluée toutes les 50 étapes. Les checkpoints intermédiaires sont conservés pour comparer leurs générations après le pilote. L'horizon du scheduler reste fixé à 1 000 étapes ; ce chiffre n'autorise pas leur exécution. Toute continuation doit conserver données, ordre et horizon, puis utiliser le checkpoint complet. Voir [la documentation Trainer](https://github.com/huggingface/transformers/blob/main/docs/source/en/trainer_recipes.md) et [TRL](https://huggingface.co/docs/trl/v0.23.1/sft_trainer).

Le runner GPU est **implémenté et son préflight testé**, mais son exécution complète n'est pas encore prouvée. Il vérifie les labels avant entraînement et les fichiers de reprise après celui-ci. La recharge et la reprise effectives sur T4 devront être confirmées avant toute prolongation. Aucune amélioration médicale ne peut être déduite des tests locaux. Le paquet externe n'a pas été envoyé ; aucun nouveau notebook, dataset ni entraînement Kaggle n'a été lancé pendant cette étape.

Le [manifeste du paquet pilote](SFT_V2_PILOT_PACKAGE_2026-09-11.json) décrit le paquet local autonome `artifacts/sft-v2-pilot-ready`. Son préflight a été exécuté depuis ce répertoire avec `--data data --tokenizer tokenizer`, sans modèle chargé et sans entraînement. Il contient uniquement train/validation, tokenizer, configuration et code ; aucun texte de test ni poids v5. Le transfert externe reste non effectué. L'environnement temporaire CPU (180 Mio apparents) a été retiré après les preuves ; les rapports et checkpoints synthétiques restent archivés.
