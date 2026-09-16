# Raccord du checkpoint courant au DPO

- Date : 2026-09-12
- Statut : draft — vérification locale effectuée, entraînement DPO non lancé
- Sources : [audit de mission](AUDIT_ALIGNEMENT_MISSION_2026-09-12.md), [archive SFT](SFT_V22_CHECKPOINT_ARCHIVE_2026-09-12.json), [identité retenue](../../configs/sft-v22-handoff.json), [comparaison convertie](SFT_V22_DPO_COMPARISON_2026-09-12.json), [longueurs DPO](DPO_PREFLIGHT_LENGTHS_2026-09-12.json).
- Environnement : macOS, worktree `codex/complete-poc-evaluation`, Python du projet principal avec `PYTHONPATH=src`.

## Changement et preuve

Le runner ne dépend plus du hash SFT v5. Il reçoit `--sft-manifest` et vérifie les poids, la configuration de l'adaptateur, le tokenizer et le chat template avant tout chargement de modèle. La base et sa révision sont prises dans ce manifeste ; la comparaison doit concerner exactement les mêmes poids. Les contrôles de revue des données, confidentialité et isolation restent actifs.

Les cinq fichiers du checkpoint général v22 à 500 étapes correspondent aux hashes de l'archive déjà conservée. Le tokenizer local se charge et rend les prompts DPO. Les 512 paires train et 64 validation existantes respectent les plafonds de 1 024 tokens pour le prompt et 2 048 pour chaque séquence complète ; maxima complets respectifs : 1 639 et 1 116 tokens. Aucune troncature n'a été appliquée.

La comparaison au format attendu par DPO est dérivée des mesures v22 existantes. Son lien au résumé GPU et au hash des poids a été contrôlé ; aucune nouvelle inférence ni nouvelle mesure de qualité n'a été faite. Ce document ne constitue pas la décision d'acceptation DPO.

Tests ciblés : `PYTHONPATH=src python -m pytest tests/test_dpo.py -q` : **5 passed**. Ils couvrent identité du checkpoint et du tokenizer, nouvelle identité SFT acceptée, comparaison d'un autre checkpoint refusée, fuite de prompts et données non revues refusées. `ruff check src/triage_poc/dpo.py scripts/run_dpo.py tests/test_dpo.py` : succès.

## Commande après finalisation de la revue

```sh
PYTHONPATH=src python scripts/run_dpo.py \
  --sft-manifest configs/sft-v22-handoff.json \
  --sft-adapter artifacts/kaggle/continuation-v22-reports/source-sft-v2-continuation-500/trainer/checkpoint-500 \
  --comparison docs/evidence/SFT_V22_DPO_COMPARISON_2026-09-12.json \
  --dataset /absolute/path/to/reviewed-dpo \
  --decision /absolute/path/to/comparison-review.json \
  --output /absolute/path/to/fresh-dpo-output \
  --max-steps 20 --dry-run
```

Les chemins de dataset revu et de décision sont volontairement des paramètres, pas des approbations créées artificiellement. Le lot existant reste candidat. L'essai GPU, la référence gelée pendant l'entraînement, la sauvegarde/recharge DPO et l'effet sur les réponses ne sont pas prouvés par les vérifications locales ci-dessus. Le checkpoint 500 reste un candidat expérimental, pas un choix déclaré optimal ni cliniquement validé.

## Revue descriptive du lot existant

Le [contrôle complémentaire](DPO_CANDIDATE_REVIEW_2026-09-12.json) vérifie à nouveau les 512/64 paires contre les hashes de prompts protégés, sans lever l'exigence de revue de confidentialité. Le lot est entièrement anglais. Les étiquettes source du train sont `length=206`, `easy=105`, `hard=201` ; celles de validation sont `length=29`, `easy=10`, `hard=25`.

Dans 358/512 paires train et 41/64 paires validation, la réponse préférée est plus longue en caractères. Ce constat ne démontre ni biais causal ni supériorité de contenu. La lecture exploratoire d'une paire par type et par split montre des questions de connaissances, des cas cliniques et des sujets biologiques généraux. Certaines paires donnent le même choix final avec des explications différentes. Il serait donc incorrect de traduire systématiquement `chosen/rejected` par « décision de triage correcte/incorrecte » ou de promettre des réponses plus courtes après DPO. La revue exploratoire ne vaut pas validation exhaustive des 576 préférences.

## Actualisation de l'isolement avec le corpus corrigé

Le [contrôle du 12 septembre](DPO_CURRENT_SFT_ISOLATION_2026-09-12.json) compare les
576 prompts DPO candidats aux 4 700 prompts uniques du SFT v2.1 : **aucun recouvrement
exact normalisé**. La liste historique de protection ne contient toutefois pas
2 561 hashes de prompts courants. Le manifeste du lot final devra ajouter ces
hashes à ceux déjà protégés ; la préparation historique est encore liée au corpus
v1. Ce contrôle utilise les prompts pour l'exclusion, aucune réponse du test final.
Il ne prouve pas l'absence de paraphrases communes.

La ligne `ultramedical-train-232` contient un masque `PHONE_NUMBER` au milieu d'une
pagination de référence bibliographique. Ce masque ne prouve pas la présence d'un
contact patient ; cette altération doit être traitée explicitement lors de la revue,
sans restaurer des chiffres inventés. Le lot original est conservé.

## Scan contextuel complémentaire

Le [scan Presidio complémentaire](DPO_CONTEXT_SCAN_2026-09-12.json) a traité les
1 728 champs des 576 paires : 529 lignes portent au moins une alerte, avec 1 544
occurrences `PERSON`, 1 317 `DATE_TIME` et 614 `LOCATION`. Aucun autre type n'a été
signalé dans ce scan du lot déjà nettoyé. Le job local `val_a85d4c35d461` est terminé
avec code 0 ; les extraits détaillés restent hors Git.

Les occurrences fréquentes comprennent notamment `FcRn`, `Treg`, `BRCA1` sous
`PERSON` et `Warfarin`, `Duphaston`, `acetaminophen` sous `LOCATION`. Ces alertes ne
doivent pas être transformées automatiquement en suppressions de contenu. Le scan
ne valide pas la confidentialité des 576 paires ; il produit une file de revue.
Aucun statut d'approbation et aucune préférence clinique n'ont été créés.

Reproduction locale : le script archivé `artifacts/dpo-context-review/scan.py`
utilise `build_presidio_analyzer()` et `PII_ENTITIES` sur les champs `prompt`,
`chosen`, `rejected`, sans seuil ajouté, sans réécriture des données. Sa version,
les empreintes d'entrée et celle des résultats sont consignées dans le rapport.

## Candidat filtré et vérification des poids

Le [filtrage contextuel](DPO_FILTERING_2026-09-12.md) remplace le candidat initial
par 426 paires train et 54 validation, sans modification des lignes retenues.
Les 96 exclusions et l'ajout des prompts SFT courants à la protection sont tracés.
Ce lot reste candidat ; les descriptions précédentes de 576 paires sont historiques.

Le runner calcule désormais les empreintes des tenseurs LoRA policy/reference après
construction du trainer, exige leur égalité initiale, puis vérifie après entraînement
que la référence n'a pas changé et que la politique a changé. Les valeurs non finies
et les inventaires incohérents sont refusés. Les empreintes et résultats sont archivés
dans `weight_checks.json` avant toute déclaration de succès.

Preuve locale : `PYTHONPATH=src python -m pytest tests/test_dpo.py -q`, six tests
réussis, dont de vrais tenseurs CPU modifiés volontairement pour vérifier le refus
d'une référence modifiée, d'une politique inchangée et de NaN. Ce contrôle ne prouve
pas encore le comportement de PEFT/TRL sur GPU ni la qualité après DPO. Il compare
les états initial/final ; il ne prétend pas observer chaque instant intermédiaire.

## Préparateur indépendant du corpus historique

`prepare_dpo_candidates.py` exige maintenant `--sft-manifest` et archive son
empreinte dans le manifeste DPO, avec le nombre d'enregistrements protégés.
L'ancien chemin v1 implicite est supprimé. Le contrôle des artefacts est exécuté
avec `audit_candidate=True` car il sert ici à exclure des prompts, pas à autoriser
un entraînement SFT. Cela ne change aucun statut de revue des préférences.

Contrôle direct local du manifeste v2.1-reviewed et de son dossier : 4 700 lignes,
4 700 prompts uniques protégés, 3 721 rendus train et 479 validation conformes.
Ruff passe. La reconstruction complète depuis UltraMedical n'est pas relancée ;
le candidat filtré existant reste intact. Cette correction rend le futur préparateur
cohérent avec la protection déjà ajoutée au candidat filtré.

## Vérification de l'artefact sauvegardé

`scripts/verify_dpo_artifact.py` permet, après un run terminé, de relier le fichier
safetensors sauvegardé aux empreintes réelles des tenseurs enregistrées après le
trainer. Il relie également les empreintes initiales de la référence au fichier SFT
vérifié, recalcule les contrôles policy/reference, et vérifie le vocabulaire et le
chat template. Le changement intentionnel du padding dans le runner est distinct
du vocabulaire et ne vaut pas changement des textes d'entrée.

```sh
PYTHONPATH=src python scripts/verify_dpo_artifact.py \
  --run /path/to/completed-source-dpo-v27 \
  --sft-manifest configs/sft-v22-handoff.json \
  --sft-adapter artifacts/kaggle/continuation-v22-reports/source-sft-v2-continuation-500/trainer/checkpoint-500 \
  --output /path/to/fresh-artifact-check.json
```

Preuve locale : huit tests DPO passent, avec de vrais fichiers safetensors
synthétiques. Ils couvrent l'égalité fichier/mémoire, un fichier altéré, des valeurs
non finies et un résumé associé au mauvais SFT. Une erreur d'insertion locale a été
détectée par les tests et corrigée avant validation ; elle n'a pas été envoyée dans
le notebook v27 déjà figé. Ruff passe. Le vérificateur n'affirme pas encore une
recharge d'inférence identique ni une qualité DPO : ces preuves restent séparées.
