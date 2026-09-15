# Vérification v20 — recharge exacte, checkpoints comparés, qualité non acquise

- **Date :** 2026-09-11
- **Statut :** draft — mesures terminées, modèle final non retenu
- **Environnement :** Kaggle privé `pierrepluton/chsa-source-sft-qwen3`, T4 gratuite, v20 / scriptVersionId `349029008`.
- **Sources :** [manifest de lancement](SFT_V20_RELOAD_LAUNCH_2026-09-11.json), [preuve de recharge](SFT_V20_RELOAD_RESULT_2026-09-11.json), [comparaison calculée](SFT_V20_CHECKPOINT_COMPARISON_2026-09-11.json), [revue des sorties](SFT_V20_OUTPUT_REVIEW_2026-09-11.json), [résultat v19](SFT_V19_PILOT_RESULT_2026-09-11.md).

## Question, entrées et exécution

La sauvegarde du pilote reproduit-elle ses résultats dans une nouvelle session GPU ? Les checkpoints 50 ou 100 répondent-ils mieux que 150 ? V20 recharge la base figée puis les adaptateurs v19. Les mêmes 479 références de validation et 30 prompts sont évalués en greedy, plafond de 512 tokens, EOS natif. Zéro donnée test et **zéro étape d’optimisation**.

L’entrée est sélectionnée par l’empreinte du résumé v19, puis les hashes du checkpoint final sont vérifiés. Les checkpoints restent archivés ; aucune prolongation du SFT n’est exécutée. Les versions et la configuration exacte sont conservées dans le résultat JSON. Le champ historique `prepared_not_launched` de cette configuration n’est pas un statut d’exécution : elle est volontairement immuable pour vérifier les hashes.

## Résultat de recharge

Kaggle termine avec `COMPLETE`. Le runner produit `pilot_fresh_reload_verified` : **30/30 générations identiques**, textes et identifiants de tokens compris, et écart absolu de loss **5,960464477539063 × 10⁻⁸**, inférieur à la tolérance technique préfixée de 10⁻⁵. Les 392 tenseurs LoRA restent en FP32. L’empreinte de l’adaptateur 150 correspond à l’archive v19.

Cela prouve la recharge en inférence du pilote dans cette pile CUDA. La reprise de l’optimiseur a été observée séparément en v19 sur deux étapes supplémentaires. Une équivalence bit à bit entre une longue exécution continue et une longue exécution reprise n’a pas été mesurée.

## Comparaison des checkpoints

| Mesure | Base | 50 étapes | 100 étapes | 150 étapes |
|---|---:|---:|---:|---:|
| Loss moyenne par exemple, 479 validations | 1,456922 | 0,821578 | 0,730581 | 0,712133 |
| Terminaison EOS, 30 réponses | 20 | 26 | 25 | 22 |
| Plafond atteint | 10 | 4 | 5 | 8 |
| Fraction moyenne de 4-grammes répétés | 0,3447 | 0,1401 | 0,1540 | 0,2426 |
| Accord textuel strict à la référence, 30 | 0 | 6 | 5 | 7 |
| Accord des choix QCM, revue assistée, 15 FR | 5 | 6 | 5 | 7 |
| Terminaison EOS, 15 EN | 9 | 11 | 10 | 7 |

La revue des choix accepte les introductions mais refuse les propositions manquantes ou supplémentaires. Aux étapes 50 et 100, les choix conformes sont aussi les correspondances textuelles strictes. Ce n’est pas le cas de Base, dont plusieurs choix conformes sont accompagnés d’explications.

À 50 étapes, trois réponses anglaises ne font que répéter la question (indices figés 0, 9, 14). À 100 étapes, l’indice 8 reformule la question sans y répondre. Plusieurs autres sorties contredisent leurs références. Les réponses courtes ne doivent donc pas être comptées comme un succès de contenu.

Le checkpoint 150 améliore certains choix français, mais augmente les répétitions et plafonds anglais par rapport à 50. La baisse de loss ne permet pas de trancher en faveur d’un entraînement plus long.

## Décision et limites

**Le contrôle technique du pilote est satisfait dans le périmètre testé. Le contrôle qualitatif ne l’est pas.** Aucun checkpoint n’est promu comme résultat SFT final et aucune poursuite automatique vers 1 000 étapes ou DPO n’est lancée.

Les contrôles de provenance, labels et isolation restent acquis, sans certification médicale du corpus ni garantie d’absence de toute fuite sémantique. Le test de 500 lignes reste réservé. Les 30 générations sont un outil de développement ; leur utilisation répétée interdit de les présenter comme une évaluation finale indépendante.

Une piste descriptive concerne le style documentaire MedQuAD : 291 réponses train comportant le marqueur HPO représentent 28,4 % du volume total des tokens de réponse. Cela ne prouve pas une cause et ne mesure pas leur poids réel dans les gradients. La prochaine expérience doit isoler une modification de style ou de sélection du train, en conservant validation/test, provenance et budget comparables. Il ne faut ni réécrire les références pour améliorer les scores, ni compter sur DPO pour réparer une pipeline non maîtrisée.

Le passage des QA médicales à un assistant de triage structuré reste également une étape distincte du mandat. Ces métriques ne mesurent ni les priorités de triage ni la sûreté clinique.

## Reproduction locale de la synthèse

```sh
PYTHONPATH=src /Users/ppluton/Documents/ChatGPT/Medical_train_llm/.venv/bin/python \
  scripts/summarize_pilot_checkpoints.py \
  --config configs/sft-v2.1-pilot.json \
  --canonical data/processed/source-sft-v2.1-reviewed/source-sft-v2.1.jsonl \
  --pilot artifacts/kaggle/pilot-v19-reports/source-sft-v2-pilot \
  --reload artifacts/kaggle/pilot-v20-reports/pilot-reload-verification \
  --output docs/evidence/SFT_V20_CHECKPOINT_COMPARISON_2026-09-11.json
```

La commande a terminé avec code 0 sur les artefacts téléchargés. Le générateur local de notebook a depuis été renforcé pour copier les checkpoints avant la vérification ; v20 avait effectué cette copie après la vérification réussie. Cette modification ultérieure ne doit pas être présentée comme exécutée en v20.
