# Diagnostic v21 — douze réponses apprises, généralisation non mesurée

- Date : 2026-09-11
- Statut : draft — objectif technique du diagnostic atteint
- Environnement : notebook privé `pierrepluton/chsa-source-sft-qwen3`, version 21, T4 gratuite, Qwen3-1.7B-Base et pile épinglés.
- Sources : [protocole](../technical/SFT_MEMORIZATION_DIAGNOSTIC_2026-09-11.md), [configuration](../../configs/sft-memorization-12.json), [lancement](SFT_MEMORIZATION_V21_LAUNCH_2026-09-11.json), [résultat calculé](SFT_MEMORIZATION_V21_RESULT_2026-09-11.json).

## Question

La pipeline corrigée permet-elle au modèle d’apprendre douze questions-réponses courtes effectivement présentes dans le train ? Le test est volontairement fait sur des exemples vus, sans prétendre mesurer la qualité sur des questions nouvelles.

## Mesures observées

Kaggle termine avec `COMPLETE`. Le runner exécute **300 étapes, soit 25 passages sur douze exemples**, avec 392 tenseurs LoRA modifiés, finis et conservés en FP32. Les logs rapportent environ **142,2 secondes de phase d’entraînement**, évaluations périodiques incluses ; installation, préparation, génération initiale/finale et publication des sorties s’ajoutent.

| Mesure sur les douze exemples train | Base | Après diagnostic |
|---|---:|---:|
| Réponses identiques après normalisation | 0/12 | 12/12 |
| Texte strictement identique après retrait des espaces en bordure | 0/12 | 12/12 |
| Arrêt par EOS natif | 9/12 | 12/12 |
| Loss moyenne de réponse sur train | 1,155250 | 0,000078016 |

Le zéro initial désigne une correspondance textuelle, pas nécessairement zéro choix QCM conforme. Le résultat final ne dépend pas seulement d’une normalisation permissive : les douze textes sont identiques aux références, à espaces de bordure près. Quatre exemples viennent de chaque source : MedQuAD, MediQAl et FrenchMedMCQA.

Les losses intermédiaires sur le même lot valent 0,000610758 à 100 étapes et 0,000096341 à 200 étapes. Les réponses intermédiaires n’ont pas été générées ; ces losses ne prouvent pas un 12/12 à ces étapes.

## Ce que cela prouve

**Prouvé sur ce lot et dans cette configuration :** les réponses sources traversent le rendu, les labels et l’optimisation, puis sont reproduites à l’inférence avec un arrêt correct. L’hypothèse d’une incapacité générale de la pipeline corrigée à apprendre ces sources n’est pas soutenue par cet essai.

**Non prouvé :** généralisation, apprentissage des longues réponses, adéquation de tous les exemples, performance de triage ou vérité médicale actuelle des références. Le learning rate, l’accumulation et l’exposition par exemple diffèrent du pilote général : ce test ne valide pas à lui seul ses hyperparamètres.

Aucune référence de validation/test n’est apprise ici. Le mode charge le fichier parent de validation pour contrôler son intégrité puis le remplace en mémoire par les douze exemples train avant tout calcul modèle. Les poids du diagnostic ne doivent jamais remplacer ceux du SFT général ni être utilisés pour DPO.

## Décision pour avancer

Il n’y a pas de raison démontrée de réécrire ou d’écarter maintenant les sources de l’école. Le pilote général n’avait couvert qu’environ 0,32 époque, tandis que cet exercice répète 25 fois chaque exemple. Cette différence invite à tester un budget d’apprentissage supplémentaire sur le corpus complet ; elle ne garantit pas une amélioration sur validation.

La prochaine expérience proposée est une **reprise bornée du checkpoint général v19**, avec corpus/ordre/scheduler conservés, jusqu’à un premier passage complet environ, puis une comparaison des réponses et des pertes par source. Elle doit réutiliser l’état optimiseur complet et conserver les checkpoints antérieurs. Cette continuation n’est pas lancée ni implémentée dans cette étape. Aucun SFT complet ni DPO ne découle automatiquement du 12/12.

## Reproduction

```sh
PYTHONPATH=src python scripts/summarize_memorization.py \
  --run artifacts/kaggle/memorization-v21-reports/train-memorization-12 \
  --manifest configs/sft-memorization-12.json \
  --launch docs/evidence/SFT_MEMORIZATION_V21_LAUNCH_2026-09-11.json \
  --canonical data/processed/source-sft-v2.1-reviewed/source-sft-v2.1.jsonl \
  --output docs/evidence/SFT_MEMORIZATION_V21_RESULT_2026-09-11.json
```

Cette commande a terminé avec code 0. Elle vérifie les hashes de corpus, de manifest et de code exécuté, l’ordre des générations et l’appartenance au train, puis recalcule les comptes. Les sorties brutes et checkpoints restent hors Git. Le code exécuté et le runner du commit `8440617` ont des AST identiques ; seuls des retours à la ligne de mise en forme diffèrent.

Validation locale : `val_d2798b416baa`, 118 tests réussis, une dépréciation Starlette/httpx ; neuf tests ciblés et Ruff réussis. Ces preuves logicielles sont distinctes du résultat GPU ci-dessus.

## Archive

La [sauvegarde complète à 300 étapes](SFT_MEMORIZATION_V21_ARCHIVE_2026-09-11.json) est téléchargée et ses empreintes correspondent au résumé GPU, avec optimiseur, scheduler, RNG, scaler et tokenizer. La copie du résumé du pilote général conservée par v21 est identique à v19. La recharge GPU de ces poids diagnostiques n’a pas été exécutée ; la preuve de recharge v20 concerne le pilote général.
