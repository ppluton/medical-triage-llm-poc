# Comparaison Base/SFT sur Kaggle — validation v8

- **Date :** 2026-09-05
- **Statut :** draft — mesure observée, génération à diagnostiquer
- **Sources :** notebook privé `pierrepluton/chsa-source-sft-qwen3`, version 8 (`347460598`), résumé et sorties téléchargés, tokenizer archivé v5.

## Conclusion et périmètre

**Proven :** le SFT augmente la vraisemblance des réponses sources sur les 500 validations appariées. **Non prouvé :** amélioration des réponses médicales, sûreté ou triage. Les sorties SFT présentent des répétitions et atteignent toutes le plafond de génération. La décision technique est `hold_for_generation_diagnostic` ; elle n'autorise pas le passage DPO.

## Environnement et reproduction

Tesla T4, PyTorch `2.10.0+cu128`, Transformers `5.5.0`, PEFT `0.18.1`, bitsandbytes `0.50.2`. Base épinglée et adaptateur SFT v5, mêmes tokens et 4 bits par défaut de bitsandbytes pour les deux variantes. Ce chargement Transformers est différent du backend Unsloth d'entraînement ; cette différence doit être examinée pendant le diagnostic.

Commande du code archivé : `run_model_comparison.py --validation … --metadata … --sft-adapter … --output …`, soit 500 validations, 30 générations par modèle, seed 42, décodage greedy, 256 tokens maximum, aucun test final.

Artefacts privés locaux : `artifacts/kaggle/base-sft-v8/`. Le code réellement exécuté est inclus dans `comparison-code/`. Ses checksums et ceux des métadonnées téléchargées correspondent au résumé. Le recalcul local de `paired_report` retrouve exactement les agrégats et les 500 identifiants/empreintes d'entrée appariés.

Résumé publiable sans textes sources : [BASE_SFT_KAGGLE_V8_SUMMARY.json](BASE_SFT_KAGGLE_V8_SUMMARY.json), SHA-256 `5f17eccce3fdf0ac72ec54f12e930f72ccc358a0fe47a832c016579cc01b9aba`. Décision liée à ce hash : [revue technique](BASE_SFT_KAGGLE_V8_REVIEW.json).

## Mesures

| Groupe | Exemples | Loss réponse Base | Loss réponse SFT |
|---|---:|---:|---:|
| Ensemble | 500 | 2,10444 | 1,52624 |
| Français | 250 | 3,60476 | 2,34005 |
| Anglais | 250 | 1,95303 | 1,44411 |
| FrenchMedMCQA | 100 | 3,27068 | 2,20896 |
| MediQAl | 150 | 3,95655 | 2,47809 |
| MedQuAD | 250 | 1,95303 | 1,44411 |

La perplexité des réponses passe de 8,2025 à 4,6008. Les 500 références ont une loss moyenne de réponse inférieure avec SFT. La loss séquence passe de 3,10337 à 1,60957.

L'ensemble est pondéré par les tokens : 61 395 tokens EN contre 6 196 FR. Il ne faut pas interpréter cet agrégat comme un score équilibré FR/EN. Langue et source sont en partie confondues.

## Résultats négatifs de génération

| Mesure descriptive | Base | SFT |
|---|---:|---:|
| Générations | 30 | 30 |
| Atteignent 256 tokens | 15 | 30 |
| Contiennent des caractères CJK | 0 | 6 |
| Latence médiane brute | 13,71 s | 26,31 s |

Des répétitions de texte et de chiffres sont visibles. Ces latences sont celles d'une génération Transformers sur GPU partagé, sans exclusion de warmup, avec longueurs différentes ; ce ne sont pas les performances de l'API vLLM.

Le script v8 ne conserve pas les identifiants des tokens générés. Le comptage au plafond n'établit donc pas à lui seul que le modèle ne produit aucun marqueur de fin de message. Un diagnostic distinct conserve ces identifiants.

## Hypothèses et décision suivante

Le tokenizer sauvegardé utilise EOS `<|endoftext|>` (151643), tandis que le template ferme les messages avec `<|im_end|>` (151645). La comparaison des vocabulaires Base/SFT sur la révision épinglée ne trouve aucun identifiant différent parmi 151 669 tokens. Le marqueur de fin reste une hypothèse, pas une cause démontrée de tous les défauts.

La version 9 devait tester trois validations déjà consultées, avec le même protocole et un arrêt supplémentaire sur `<|im_end|>`. Aucun entraînement ou test final n'est lancé. Selon le résultat, vérifier également le chargement/quantification et le backend d'entraînement avant de décider un nouveau SFT ou un DPO.

## Incidents de préparation

Les versions 6 et 7 ont échoué avant mesure complète : sorties v5 non attachées, puis chemins d'adaptateur ambigus. La version 8 attache explicitement les sorties v5 et sélectionne l'adaptateur par SHA-256. Les exécutions sont restées privées sur quota gratuit.

### Résultat du diagnostic v9

Échec avant inférence : Kaggle a attaché les sorties v8, alors que la demande explicite à kagglehub exigeait v5. Le backend refuse d'attacher une nouvelle source en session non interactive. Aucun résultat ne permet donc encore de confirmer ou réfuter l'hypothèse du marqueur de fin.

Le builder a été corrigé pour chercher exclusivement des entrées déjà montées et validées par checksum, sans résolution implicite de dernière version. Un paquet minimal de cinq fichiers (81,2 Mo, poids et tokenizer, aucun texte source/patient) a été téléversé après autorisation explicite dans `pierrepluton/chsa-sft-v5-adapter` (ID 11908435). Kaggle confirme `ready` et `isPrivate: true`. La version 10 du notebook est lancée avec cet attachement stable, trois validations et l'arrêt EOS/message-end. Son résultat reste à analyser.

### Diagnostic v10 : marqueur de fin

Le run v10 est terminé. Les cinq fichiers du dataset privé ont été retéléchargés et leurs SHA-256 correspondent aux originaux. Le résumé [v10](BASE_SFT_KAGGLE_V10_SUMMARY.json) a pour SHA-256 `fefca1a7a1bd55821c53c0f70dfb8514d2b3cfa565ffd8349ae4f5b9f2d81081`.

Sur les trois mêmes validations, avec `eos_token_id=[151643,151645]`, les sorties SFT atteignent toutes 256 tokens et ne contiennent aucun de ces deux tokens. Base termine deux sorties sur EOS (114 et 159 tokens), la troisième atteint 256. L'ajout du marqueur de fin ne corrige donc pas les défauts sur cet échantillon. Il ne suffit pas de changer le paramètre d'arrêt.

La version 11 compare maintenant les mêmes trois validations avec NF4/double quantification/calcul FP16 puis sans quantification (FP16). Aucun entraînement ni test final. Le résultat départagera un problème de quantification d'un défaut persistant ; il ne permettra pas, à lui seul, d'attribuer ce défaut à l'entraînement plutôt qu'au backend.

### Diagnostic v11 : quantification

Le run v11 est terminé : en NF4/double quantification/FP16 comme en FP16 sans quantification, les trois générations SFT atteignent 256 tokens sans EOS/message-end. Les répétitions persistent dans les deux chargements. Les textes diffèrent, mais aucun chargement testé ne résout le défaut sur cet échantillon.

Résumés sans textes : [NF4](BASE_SFT_KAGGLE_V11_NF4_SUMMARY.json), [FP16](BASE_SFT_KAGGLE_V11_FP16_SUMMARY.json). Artefacts et code exécuté : `artifacts/kaggle/diagnostic-v11/`. Cette mesure réfute une correction par la seule quantification ; elle n'identifie pas encore la cause d'entraînement ou de backend.

La version 12 exécute le même contrôle avec Unsloth et les versions de dépendances du run SFT original. Le runner `scripts/diagnose_sft_unsloth.py` conserve également les normes des embeddings des marqueurs. Aucun nouvel entraînement n'est lancé à cette étape.
