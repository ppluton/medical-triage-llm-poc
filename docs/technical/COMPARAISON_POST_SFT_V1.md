# Comparaison post-SFT et préparation DPO

- **Date :** 2026-09-05
- **Statut :** draft — implémentation locale, exécutions GPU à consigner séparément
- **Sources :** brief, spécification, ADR-010, manifeste SFT, scripts associés ; [PEFT](https://huggingface.co/docs/peft/package_reference/peft_model), [TRL 0.23.1 DPO](https://huggingface.co/docs/trl/v0.23.1/en/dpo_trainer).

## Question et protocole

L'adaptateur SFT attribue-t-il une meilleure probabilité aux réponses sources sur validation, et comment ses générations diffèrent-elles de Base ? La comparaison utilise `unsloth/Qwen3-1.7B-Base` à la révision `e249956c10337100486d07afb77e3eb2b30906b8`, le tokenizer archivé et 500 conversations de validation dont le SHA-256 est figé. Aucun texte du test final n'est envoyé à Kaggle par cette étape.

`run_model_comparison.py` charge une seule base en 4 bits puis désactive ou active l'adaptateur. Les entrées tokenisées, la seed 42 et les paramètres de génération restent identiques. Le préfixe exact est vérifié ; la réponse attendue est exclue des entrées de génération. Deux mesures sont produites : loss des tokens de réponse et loss de toute la séquence, chacune pondérée par son nombre de tokens. La seconde n'est pas nécessairement identique à l'`eval_loss` du trainer, dont l'agrégation peut différer.

Les résultats sont ventilés par langue et source. Trente conversations sélectionnées de façon déterministe produisent des réponses avec un maximum de 256 nouveaux tokens. Ces sorties et leurs références restent hors Git. Leur revue est `pending`. Une meilleure vraisemblance n'est pas une preuve de réponse médicalement correcte.

## Commandes

```bash
PYTHONPATH=src python scripts/build_comparison_notebook.py \
  --artifacts /path/to/source-sft-v1 \
  --output notebooks/kaggle-base-sft-comparison.ipynb
```

Le builder vérifie les artefacts du manifeste local avant de n'exporter que des métadonnées de validation. Le notebook lit les entrées déjà montées et exige le checksum exact du SFT v5. Le run v9 a prouvé que `kernel_sources: ["pierrepluton/chsa-source-sft-qwen3/5"]` ne fige pas la version : Kaggle a attaché la dernière sortie réussie v8. Le builder ne tente donc plus de résoudre cet attachement automatiquement.

Avant une nouvelle exécution, attacher explicitement l'adaptateur archivé v5 ou son ZIP original, en conservant le dataset de validation privé existant. Le dataset privé `pierrepluton/chsa-sft-v5-adapter` a été créé avec autorisation explicite (ID 11908435, `isPrivate: true` vérifié par les métadonnées Kaggle). La version 10 du notebook utilise cet attachement et aucun `kernel_sources`. Le paquet minimal contrôlé est dans `artifacts/sft-v5-kaggle-attachment` (81 216 320 octets hors manifeste).

Le notebook installe Transformers 5.5.0, PEFT 0.18.1, Accelerate 1.14.0, bitsandbytes 0.50.2. Ces dépendances CUDA sont distinctes du runtime local du projet, dont Transformers reste inférieur à 5. Les versions effectives sont enregistrées par le run.

## Préparation DPO

```bash
PYTHONPATH=src python scripts/prepare_dpo_candidates.py \
  --source /path/to/ultramedical-preference/data \
  --index /path/to/ultramedical-preference-reconstruction-index-v1.jsonl \
  --sft-artifacts /path/to/source-sft-v1 \
  --output artifacts/dpo-candidates-v2
```

Le script vérifie les checksums de la source et de l'index, sélectionne 64 validations puis 512 candidats train, exclut les prompts SFT et ceux réservés au test UltraMedical, vérifie la correspondance des conversations, applique Presidio aux identifiants directs et refuse les doublons après anonymisation. Il conserve provenance, préférence source et statuts de revue. Les octets du test UltraMedical ne sont lus que pour vérifier le checksum source ; ses réponses ne sont pas utilisées pour construire les candidats.

La sélection utilise l'ordre source et un plafond de 6 000 caractères par texte : elle n'est ni représentative ni équilibrée. La langue EN vient du périmètre de source et doit être confirmée à la revue. Le premier essai avec NER complet a été rejeté car il masquait des termes médicaux. Le second conserve les noms, lieux et dates ; une revue complémentaire de confidentialité est donc obligatoire. Le statut `passed_direct_identifiers_only` ne signifie pas anonymisation complète. Les références hachées protègent des recouvrements textuels exacts, pas des paraphrases.

## Passage à l'entraînement

`run_dpo.py --dry-run` exige : une comparaison Base/SFT terminée avec le bon SFT et zéro test, une décision `accepted_for_educational_dpo` liée au checksum exact du résumé, un reviewer et une justification, et un manifeste de données `approved_for_educational_dpo`.

Ces statuts ne sont jamais attribués automatiquement par le préparateur. Une approbation technique ne satisfait pas la validation clinique exigée par le brief. `configs/dpo.yaml` décrit la recette ; le runner construit et archive sa `DPOConfig` effective. Les dépendances proposées du runner DPO sont épinglées dans `requirements/dpo-kaggle.txt` ; leur exécution CUDA reste à prouver séparément du runtime de comparaison. La recette expérimentale utilise TRL 0.23.1, deux copies de l'adaptateur SFT (politique entraînable et référence figée), beta 0,1, LR `5e-6`, batch effectif 8 et 20 étapes par défaut. Les limites sont 1–500 étapes, 1 024 tokens de prompt et 2 048 par séquence ; le pré-vol refuse les dépassements.

```bash
PYTHONPATH=src python scripts/run_dpo.py \
  --dataset artifacts/dpo-reviewed-v1 \
  --comparison /path/to/base-sft/summary.json \
  --decision /path/to/comparison-review.json \
  --sft-adapter /path/to/best-adapter \
  --output artifacts/dpo-smoke-v1 --max-steps 20 --dry-run
```

L'adaptateur DPO est sauvegardé sous `adapter/policy`. Rejouer ensuite la comparaison avec `--dpo-adapter /path/to/adapter/policy`. Le test final, la revue de sûreté et le choix d'un checkpoint destiné à la démonstration restent des étapes distinctes.

## Sonde synthétique additionnelle

`build_comparison_notebook.py --include-synthetic-probe` ajoute le protocole `configs/synthetic-schema-probe-v1.json` au notebook. Il contient les huit catégories des fixtures de développement, des contextes explicitement `synthetic`, le prompt proposé de l'API et son schéma JSON. Les anciens `expected_level` proposés sont volontairement absents du protocole.

Après les mesures QA, le runner active chaque checkpoint à son tour et génère au maximum 512 tokens par cas. Il conserve les réponses brutes, le nombre de tokens, la latence et la validité JSON/schema. Le décodage n'est pas contraint : il mesure l'adhésion spontanée au format, distincte d'un serveur vLLM avec décodage contraint. Aucun score clinique ou de sous-triage n'est calculé sur ces fixtures. Le notebook généré et son Python sont vérifiés localement ; cette sonde n'a pas été exécutée dans le run Kaggle v8, qui utilise le protocole QA initial.

## Reproduire les diagnostics courts

Ajouter `--count 3 --generate-count 3 --stop-on-message-end` au builder. `--precision` accepte `4bit-default`, `4bit-nf4` (NF4, double quantification, calcul FP16) et `float16`. Les paramètres et la configuration de quantification effective sont archivés dans le résumé. Changer de répertoire de sortie entre les runs ; les anciens résultats ne sont jamais écrasés.

Le diagnostic v10 a réfuté la correction par le seul arrêt de message sur trois exemples : zéro token de fin émis par SFT avant le plafond. Voir la preuve comparative pour les résultats des expériences suivantes.

Le diagnostic original utilise `diagnose_sft_unsloth.py --validation … --sft-adapter … --output …` avec les dépendances du SFT v5. Le run v13 confirme les défauts avec Unsloth. La cause précise et la correction du SFT restent à établir ; une comparaison ne doit pas être déclarée acceptable sur la seule loss.
