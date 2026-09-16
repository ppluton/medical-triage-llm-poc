# Pilote SFT v19 — mécanique validée, progrès partiels et limites qualitatives

- **Date :** 2026-09-11
- **Statut :** draft — pilote terminé ; recharge finale et comparaison des checkpoints vérifiées
- **Environnement :** notebook Kaggle privé `pierrepluton/chsa-source-sft-qwen3`, v19, scriptVersionId `349021973`, T4 gratuite.
- **Sources :** [lancement et versions](SFT_V2_PILOT_V19_LAUNCH_2026-09-11.json), [archive du checkpoint](SFT_V19_CHECKPOINT_ARCHIVE_2026-09-11.json), [métriques appariées](SFT_V19_PAIRED_METRICS_2026-09-11.json), [revue textuelle des sorties](SFT_V19_OUTPUT_REVIEW_2026-09-11.json).

## Question et protocole

Vérifier qu'un pilote depuis la base, sur le corpus audité, peut apprendre et sauvegarder un état reprenable sans engager un SFT complet. Corpus : 3 721 train, 479 validation ; zéro test utilisé. Seed 42, loss sur réponse seule, LoRA neuf, budget de 150 étapes ou 1 800 secondes, horizon du scheduler maintenu à 1 000 étapes.

L'évaluation appariée emploie 479 références et 30 générations greedy figées, réparties en 15 réponses anglaises MedQuAD et 15 QCM français. Le plafond reste fixé à 512 tokens pour Base et Pilote. Les références ne sont pas certifiées comme vérité médicale actuelle.

## Résultat d'exécution

Kaggle indique `COMPLETE`. Les 150 étapes comportent des losses et normes de gradient finies. Les 392 tenseurs de l'adaptateur ont changé et restent finis. La phase d'entraînement dure environ **701 secondes**, soit 11 min 41 s, évaluations périodiques incluses ; préparation, smokes, baseline et évaluation finale sont supplémentaires.

L'état final correspond à environ **0,3225 époque**, pas à un SFT complet. Il contient adaptateur, optimiseur, scheduler, RNG, scaler AMP et état du trainer. Les empreintes locales correspondent au manifest produit pendant l'exécution. SHA-256 de l'adaptateur final : `9674c6a12a903eb969d70eae089d915a52e04b5ea0c50f875b090297b9ccbb01`.

La vérification préalable a également prouvé une recharge identique sur deux générations puis une reprise de l'optimiseur de l'étape 2 à l'étape 4. La v20 a ensuite vérifié le checkpoint final à 150 étapes dans une nouvelle session GPU : 30 générations identiques, écart de loss de 5,96 × 10⁻⁸ sur 479 exemples, aucune étape d’optimisation.

## Mesures appariées

| Mesure | Base | Pilote 150 |
|---|---:|---:|
| Loss moyenne par exemple, réponse seule, 479 validations | 1,456922 | 0,712133 |
| Terminaison EOS native, 30 générations | 20/30 | 22/30 |
| Plafond de 512 tokens atteint | 10/30 | 8/30 |
| Correspondance textuelle normalisée à la référence | 0/30 | 7/30 |
| Fraction moyenne de 4-grammes de tokens répétés | 0,3447 | 0,2426 |

La loss aux étapes 50 et 100 vaut respectivement **0,821578** et **0,730581**. Ces baisses ne constituent pas une mesure d'exactitude clinique.

| Sous-ensemble | EOS Base → Pilote | Plafond Base → Pilote | Accord textuel exact Base → Pilote |
|---|---:|---:|---:|
| MedQuAD EN, 15 | 9 → 7 | 6 → 8 | 0 → 0 |
| MediQAl FR, 9 | 6 → 9 | 3 → 0 | 0 → 5 |
| FrenchMedMCQA FR, 6 | 5 → 6 | 1 → 0 | 0 → 2 |

Le total masque donc une dégradation du taux de terminaison en anglais, malgré une amélioration nette du format français. Aucun texte de sortie n'est strictement vide ; cinq réponses Base très courtes sont toutefois des fragments non répondants, que le compteur « vide » ne détecte pas.

## Revue des réponses, distincte de l'exact match

Une revue textuelle assistée par Codex compare les ensembles de réponses sélectionnées aux références des 15 QCM. Elle accepte une formulation introductive, mais rejette les choix manquants ou supplémentaires. Elle donne **5/15 accords pour Base et 7/15 pour Pilote**, avec **quatre gains et deux régressions**. L'accord peut coexister avec une réponse répétitive : il ne certifie ni l'utilisabilité de la sortie ni son explication.

Il serait incorrect de présenter le passage de 0 à 7 correspondances textuelles comme un passage de 0 à 7 réponses QCM correctes. Les identifiants, transitions et limites de cette revue sont consignés dans le JSON lié en tête.

En anglais, la revue observe encore des boucles et des contradictions explicites avec les références, notamment sur des chiffres ou des noms de gènes. Certaines réponses reprennent une structure de tableau HPO et poursuivent une liste artificielle. Les huit plafonds atteints ne s'expliquent pas simplement par la longueur des références : plusieurs sorties montrent des répétitions manifestes. À l'inverse, [trois références dépassent elles-mêmes le plafond](SFT_PILOT_REFERENCE_LENGTHS_2026-09-11.json), ce qui impose de conserver les métriques distinctes.

## Hypothèse de style documentaire à examiner

Un [inventaire descriptif](SFT_MEDQUAD_STYLE_DIAGNOSTIC_2026-09-11.json) trouve le marqueur `Human Phenotype Ontology` dans 291 des 1 746 réponses MedQuAD d'entraînement. Ces réponses représentent environ 29,3 % des caractères de ce sous-ensemble. La présence d'un texte répétitif commun est une piste pour expliquer le style appris, **pas une preuve causale**. Aucun enregistrement ni split n'a été modifié à partir de ce diagnostic.

## Verdict et prochaine étape

- **Prouvé techniquement :** contrôles de données/labels définis, mises à jour GPU, précision conservée, sauvegarde complète et archive vérifiée.
- **Partiellement prouvé :** apprentissage sur validation et amélioration de plusieurs réponses françaises.
- **Non acquis :** qualité satisfaisante des générations anglaises, amélioration générale sans régression, pertinence clinique.
- **En cours :** recharge du checkpoint final et comparaison des générations aux étapes 50/100/150, avec zéro nouvelle étape d'entraînement.

Aucun SFT long ni DPO n'est automatiquement approuvé par ce résultat. La décision doit s'appuyer sur la comparaison des sorties et les limites ci-dessus, et être expliquée avant toute nouvelle exécution d'entraînement.

## Commande de synthèse

```sh
PYTHONPATH=src /Users/ppluton/Documents/ChatGPT/Medical_train_llm/.venv/bin/python \
  scripts/summarize_sft_pilot.py \
  --config configs/sft-v2.1-pilot.json \
  --canonical data/processed/source-sft-v2.1-reviewed/source-sft-v2.1.jsonl \
  --run artifacts/kaggle/pilot-v19-reports/source-sft-v2-pilot \
  --output docs/evidence/SFT_V19_PAIRED_METRICS_2026-09-11.json
```

Les poids et les sorties textuelles restent hors Git. Les preuves publiques contiennent les métriques, identifiants et empreintes.
