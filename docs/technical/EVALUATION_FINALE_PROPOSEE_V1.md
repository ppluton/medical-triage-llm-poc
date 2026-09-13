# Protocole proposé du test final

- Date : 2026-09-13
- Statut : proposed — pas encore figé ni exécuté
- Sources : SPEC_POC_TRIAGE_MEDICAL.md, configs/final-evaluation-proposed-v1.json, COMPARAISON_MODELES_COURANTS.md.

## Question et conditions

Après les décisions de développement sur validation, comparer Base, SFT et DPO
sur le split réservé. Ne pas consulter ses réponses pour choisir checkpoint,
prompt ou hyperparamètres. Avant exécution, figer ces choix, les hashes des poids,
du tokenizer, du code, des entrées et du runtime dans un manifeste distinct.
La configuration proposée ne lance rien et ne sélectionne encore aucun exemple.

## Mesures prévues

Calculer la loss sur réponse seule et EOS natif pour les 500 exemples, avec le
même rendu que le SFT et la comparaison v28. Rapporter moyenne par exemple,
comptage, longueur et éventuels dépassements ; aucun exemple exclu silencieusement.
Pour borner la génération, sélectionner 50 identifiants par ordre croissant du
SHA-256 UTF-8 de `42:<record_id>`, puis identifiant en cas d'égalité. Vérifier
l'unicité des identifiants et conserver la liste avant toute génération. Ce choix
ne dépend ni de la réponse attendue ni des résultats d'un modèle.

Générer les mêmes 50 prompts pour les trois variantes, greedy, plafond 512 tokens.
Conserver textes, IDs de tokens, arrêt EOS, répétitions et temps. Les 50 exemples
ne garantissent pas une représentation équilibrée des langues ou sources : publier
leur composition, sans les remplacer a posteriori. La loss et l'arrêt ne sont pas
une mesure de justesse médicale. Une revue des réponses reste nécessaire ; ne pas
utiliser un score lexical comme substitut à cette revue.

Les 18 scénarios de triage déjà utilisés restent des scénarios de développement.
Les rejouer avec l'API teste l'intégration, pas la généralisation à un test inédit.
Le test QA réservé n'apporte pas de labels de priorité clinique. Toute revendication
de performance clinique reste exclue sans protocole et références cliniques validés.

## Exécution et suites

Le runner archivé v28 reste inchangé. Le script local propose désormais un mode
`--test /path/to/test --final-freeze /path/to/freeze.json`, exclusif des arguments
de développement. Son vérificateur de résultats doit encore être adapté au test
final avant de lancer ce protocole. Ne jamais renommer le test en validation.
Vérifier d'abord la fin et les résultats de v28, puis le budget gratuit disponible.
Une correction motivée par les résultats du test rend ce jeu utilisé pour le
développement ; ne pas conserver alors la qualification de test indépendant.

## Sélection locale implémentée

`triage_poc.final_selection.select_generation_ids` applique le classement décrit
ci-dessus, refuse les doublons, identifiants vides et paramètres invalides.
Vérification : `PYTHONPATH=src python -m pytest tests/test_final_selection.py -q`,
8 tests passent le 2026-09-13 sur 500 identifiants synthétiques. L'ordre d'entrée
ne modifie pas la sélection ; un autre seed la modifie ; une sélection plus petite
est le préfixe de la même liste. Aucun fichier de test réservé n'est chargé.
Cette preuve porte sur la sélection uniquement : raccord au runner et gel final
restent à réaliser.


## Raccord au runner local

Le mode final exige un manifeste avec `status: frozen`, les paramètres fixes du
protocole, les `package_versions` exactes (torch, transformers, peft, bitsandbytes)
et les `input_hashes` : test, data_manifest, sft_manifest, dpo_summary, runner,
selection et termination. Il vérifie les artefacts SFT/DPO avec les contrôles
existants. Le fichier de test doit correspondre à `test_qwen3` du manifeste source.
Aucun manifeste final n'a encore été produit : le choix dépend de v28.

La sélection et le manifeste sont sauvegardés avant les calculs. Les trois modèles
partagent les 500 loss et les 50 prompts ; aucun scénario de développement n'est
inclus dans ce mode. Le résumé indique explicitement `evaluation_split: test`
et le nombre d'exemples de test utilisés. Le mode de développement reste disponible.
Le paquet Kaggle de développement inclut le nouveau module importé ; aucune
nouvelle version distante n'a été envoyée.

Validation locale : 10 tests ciblés passent (sélection, refus du gel incomplet ou
altéré et vérificateur des résultats de développement), CLI `--help` et Ruff passent.
Cela ne prouve pas le mode final complet sur GPU. Le vérificateur final, le gel et
l'exécution restent à terminer avant d'annoncer une mesure indépendante.


### Précondition encore manquante : export du test

Le manifeste v2.1 courant contient `canonical`, `train_qwen3` et
`validation_qwen3`, mais aucun `test_qwen3`. C'est volontaire : les 500 exemples
réservés sont uniquement dans le canonique. Avant le gel final, produire un export
traçable avec le même transformateur que train/validation et un manifeste dérivé
qui lie son hash au canonique, sans modifier le manifeste historique. Le mode final
refuse explicitement un manifeste qui ne contient pas cet export. Aucun export du
test n'a été réalisé pendant cette préparation.

### Exporteur prêt, sans exécution sur le corpus réservé

`scripts/export_final_test.py --canonical /path/to/canonical.jsonl
--source-manifest /path/to/source-manifest.json --output /path/to/fresh-export`
contrôle le hash et le nombre d'enregistrements du canonique, puis exporte uniquement
les 500 lignes test avec le rendu partagé. Il écrit un manifeste dérivé avec
l'empreinte du parent et du code, sans modifier l'historique. Le renderer de train
continue de refuser le split test ; une fonction explicite d'évaluation le traite.

Dix tests ciblés passent (`tests/test_final_export.py tests/test_source_sft.py`),
ainsi que Ruff : population synthétique de 501 lignes dont 500 test, exclusion du
train, parent inchangé, hash altéré et sortie existante refusés. Aucun texte du
corpus réservé n'a été ouvert pendant cette vérification. L'export réel reste à
exécuter et vérifier avant le gel ; ces tests ne prouvent pas encore cet artefact.
