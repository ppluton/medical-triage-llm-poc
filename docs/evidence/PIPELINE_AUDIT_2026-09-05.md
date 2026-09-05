# Audit de la pipeline avant un nouvel entraînement

- **Date :** 2026-09-05
- **Statut :** draft — entraînements longs bloqués
- **Périmètre :** sources → préparation SFT → tokenizer → trainer → sauvegarde → comparaison → DPO → API.
- **Sources :** CADRAGE_MISSION.md ; SPEC_POC_TRIAGE_MEDICAL.md ; ADR-011 ; PIPELINE_AUDIT_V1.json ; SFT_LABEL_AUDIT_V14.json ; BASE_SFT_KAGGLE_2026-09-05.md ; tests locaux.
- **Environnements :** macOS CPU pour données/tests ; notebook Kaggle privé `pierrepluton/chsa-source-sft-qwen3` v14, runtime original Unsloth, pour audit des labels. Zéro étape d'entraînement dans v14.
- **Code :** branche `codex/complete-poc-evaluation`, modifications après `3092666`. Les manifestes de reconstruction enregistrent les hashes des scripts producteurs.

## Résultats observés sur v1 / SFT v5

| Contrôle | Mesure | Conclusion technique |
|---|---|---|
| Identité des artefacts | Hashes conformes ; 5 000 identifiants et questions normalisées uniques ; splits 4 000/500/500 | Proven pour l'intégrité v1 |
| Canonique → conversations | 0 différence de contenu ; test non rendu | Proven pour ce rendu |
| Longueur exacte | Maximum 1 267 tokens train / 1 199 validation ; 0 dépassement de 2 048 | Le dépassement du contexte n'explique pas le défaut observé |
| Troncature à la préparation | 80 train, 7 validation, 14 test | Défaut de complétude à corriger |
| Choix QCM | Au moins un choix absent dans 2 249 des 2 250 exemples QCM train/validation | Défaut du convertisseur ; cela ne rend pas automatiquement chaque QA inutilisable |
| EOS natif dans le rendu | 0/4 000 train ; 0/500 validation | Format incompatible avec le signal de fin attendu |
| Labels du trainer réel, v14 | Format initial : 0 EOS par exemple ; candidat : 1 EOS par exemple, sur 64 exemples chacun | Correction des labels prouvée sur ce sous-ensemble, sans entraînement |
| Embeddings début/fin | Identiques et gelés ; `tie_word_embeddings=true` dans la base épinglée | Les deux marqueurs ne sont pas discriminables par la projection liée observée |
| Générations SFT v5 | 30/30 atteignent 256 tokens ; répétitions ; 6/30 avec caractères CJK | Checkpoint non retenu comme réussite malgré une loss améliorée |

Le diagnostic auxiliaire v13 sur le token « 完整热 » était invalide : conversion en identifiant absent, puis norme d'une matrice. Il est exclu de la conclusion. Le constat v14 utilise une comparaison explicite des embeddings des marqueurs connus.

## Corrections et vérification locale

- Schéma v2 distinct ; choix inclus avant anonymisation ; rejet des exemples trop longs au lieu de couper le texte.
- Affectations historiques train/validation/test conservées pour chaque identifiant déjà présent.
- Pré-vol sur le template exact, comparaison au canonique et refus d'un EOS terminal absent ou masqué par le padding.
- Tokenizer candidat sans changement de vocabulaire ; seule la terminaison de la dernière réponse change.
- Expérience CUDA limitée à 20 étapes/64 exemples, avec modes sans entraînement ; micro-run MLX limité à 20 étapes.
- Vérification du schéma par de vrais enregistrements produits à partir de fixtures synthétiques. La reconstruction initiale v2 a échoué sur une liste de transformations restée au format v1, avant écriture des artefacts. Le schéma et son test ont été corrigés avant relance.

### Artefacts v2 réellement reconstruits et contrôlés

Le manifeste `data/manifests/derived-source-medical-qa-sft-v2.json` identifie le canonique par SHA-256 `3f754a9a4d34a15d06094b2190c0f906c71826c0998c6814109f3c8b122bd2c2`. Ses hashes de code correspondent aux fichiers producteurs présents après reconstruction.

- 5 000 exemples : 2 500 FR / 2 500 EN ; train 4 000, validation 500, test 500.
- 4 899 identifiants conservés ; 101 exemples précédemment tronqués remplacés ; **zéro migration historique de split**.
- **Zéro troncature**, 5 000 identifiants et questions normalisées uniques ; zéro différence canonique/conversations.
- Sur les **2 250 QCM train/validation**, **zéro choix source absent** après reconstruction et anonymisation.
- Les **4 500 conversations** ont un EOS terminal ; aucun padding présent dans le contenu ; maximum **1 072 tokens train / 939 validation**, sous 2 048.
- Les 4 500 prompts de génération sont identiques entre les tokenizers initial et candidat sur le corpus v2. Seul le terminateur de la réponse d'entraînement change ; vocabulaire identique. Cela ne signifie pas que les questions v1 et v2 sont identiques : les choix ont été ajoutés dans v2.
- Le test n'est jamais rendu pour l'entraînement ou la génération de développement.

Preuves : [audit v2](PIPELINE_AUDIT_V2.json), [pré-vol exact](SFT_V2_PREFLIGHT.json), [contrôle de révision](SFT_V2_REVISION_CHECK.json), [tokenizer candidat](TOKENIZER_EOS_CANDIDATE_V1.json). Les quatre commandes de reconstruction et vérification ont terminé avec le code de sortie 0. Aucun de ces résultats n'est un entraînement ou une preuve clinique.

Les contrôles locaux finaux passent : **98 tests en 19,96 s**, une dépréciation Starlette/httpx sans échec, et `ruff check src scripts tests` sans erreur. Le mode `--dry-run` de l’expérience native EOS valide les hashes et la sélection 64 train / 3 validation, avec zéro test utilisé. La sauvegarde/recharge GPU est implémentée mais reste non exécutée.

## Portes encore ouvertes

| Étape | Niveau de preuve | Ce qui manque |
|---|---|---|
| Données corrigées v2 | Proven pour les contrôles techniques ci-dessus | Revue de contenu distincte ; aucune validation clinique |
| Format EOS candidat | Partiellement prouvé | Audit de tous les labels avec les données v2 dans le runtime cible |
| SFT correctif | Non prouvé | Micro-run, variation des poids, arrêt et contenu des générations |
| Sauvegarde/recharge | Implémentée, non exécutée pour un nouveau SFT | Le micro-run recharge une base épinglée et les poids exportés, puis exige des générations identiques |
| Runner complet CUDA | Historique archivé dans le bundle privé v5 | Le runner complet historique ne figure pas dans cette branche ; intégrer et vérifier une recette v2 avant un run long |
| Comparaison corrigée | Non prouvée | Protocole v2 figé et commun ; les scripts v1 gardent leurs hashes historiques |
| DPO | Préparation implémentée, entraînement non effectué | Revue des préférences et micro-run après acceptation technique du SFT |
| API | Tests/contrats et smoke Docker antérieurs prouvés | Inférence réelle du checkpoint via serveur, latence et chaîne d'audit |
| Clinique/pilote | Non prouvé | Revue clinique documentée ; cible de déploiement explicitement autorisée |

## Reproduction

Depuis le worktree, utiliser `PYTHONPATH=src` avec l'environnement Python du projet : celui-ci est installé en mode editable sur un autre checkout. Sans cette variable, les tests pourraient charger la mauvaise version du code.

```sh
PYTHONPATH=src python -m pytest -q
PYTHONPATH=src python -m ruff check src scripts tests
PYTHONPATH=src python scripts/audit_source_sft_pipeline.py --help
PYTHONPATH=src python scripts/preflight_source_sft.py --help
PYTHONPATH=src python scripts/verify_source_sft_revision.py --help
PYTHONPATH=src python scripts/run_sft_termination_experiment.py --help
```

La commande CUDA `--audit-only` s'arrête après inspection des labels et avant `trainer.train()`. Ne pas lancer les deux bras d'entraînement sur v1 comme entraînement de production : ils servent uniquement à isoler l'effet de la terminaison sur le checkpoint historique.
