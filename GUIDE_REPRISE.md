# Reprendre ici — POC de triage médical

Date : 2026-09-16 — Statut : draft, guide de travail actif
Propriétaire : Pierre. Statut clinique : aucune validation clinique acquise.

Sources : [mission OpenClassrooms](https://openclassrooms.com/fr/paths/2053/projects/3421/8585-mission---developpez-le-poc-d'un-agent-de-triage-medical), [livrables et soutenance](https://openclassrooms.com/fr/paths/2053/projects/3421/8586-livrables-et-soutenance), [cadrage](CADRAGE_MISSION.md), [spécification](SPEC_POC_TRIAGE_MEDICAL.md). Pages relues intégralement le 16 septembre. En cas d’écart entre ce guide et les références, consigner l’écart et corriger le guide.

La [spécification d’exécution](SPEC_EXECUTION_V1.md) fixe la stack, les interfaces et les livrables. Ce guide décrit uniquement l’ordre de travail.

## Nature du projet

Le CHSA, Dr Marie Dubois et la mission de quatre semaines constituent le scénario professionnel pédagogique OpenClassrooms. Aucun hôpital réel ni référent clinique externe n'est fourni pour exécuter le projet. La « validation clinique » demandée dans ce cadre est donc mise en œuvre comme une validation de POC documentée : préférences source, grille de revue, jeux d'évaluation, métriques de sécurité et limites explicites.

Cette validation de POC permet d'avancer dans la mission ; elle ne doit pas être présentée comme l'avis d'un professionnel de santé, une étude clinique ou une autorisation d'usage réel. Une validation indépendante par des professionnels devient une condition de passage vers un pilote hospitalier réel, pas un bloqueur artificiel de la réalisation scolaire.

## Objectif et échéance

Première version des livrables demandée pour le 17 septembre 2026 à 15 h Europe/Paris, soit 17 h Asia/Tbilisi. Cette échéance ne transforme pas une limite connue en résultat validé.

Construire un assistant FR/EN qui recueille les symptômes, pose des questions utiles, propose une des trois priorités, explique sa réponse et journalise l’interaction. Démontrer Qwen3-1.7B-Base, puis SFT/LoRA, puis DPO et une API FastAPI/vLLM accessible sur le cloud avec déploiement GitHub Actions.

Nous reprenons la méthode depuis les sources. Le code, les données corrigées et les poids existants sont des candidats à réutiliser après vérification, pas des validations automatiques de la nouvelle démarche. L’historique est conservé sans réécriture des mesures.

## Règles pour avancer simplement

- Une configuration active par étape, une question par expérience, un compte rendu bref avec décision suivante.
- Conserver les sources demandées par l’école. Ne pas remplacer le corpus par des réponses de triage inventées pour améliorer un score.
- Distinguer QA médicale, comportement de triage et format JSON. Mesurer les trois sans les confondre.
- Une anomalie technique reproductible déclenche une correction ciblée. Une réponse QCM erronée ne justifie pas une série illimitée de micro-runs.
- Ne changer ni modèle, ni données, ni prompt simultanément pour expliquer un gain.
- Le jeu final v35 a déjà été consulté : il reste un résultat historique, pas un nouveau test aveugle. Tout ajustement utilise train/validation ; un nouveau test final exige une réserve réellement non consultée et isolée par groupes.
- Avant un nouveau SFT complet, présenter les données retenues, les vérifications, le petit essai, la durée estimée à partir de son débit et le coût. Ne pas garantir le gain avant mesure.
- Les budgets de temps ci-dessous sont des limites d’organisation, pas des seuils cliniques. Les seuils médicaux restent proposés jusqu’à revue compétente.

## 0 — Cadrer la reprise

**À produire :** ce guide, un retour d’expérience et la liste des livrables. Relire les étapes 0 à 3 et la soutenance ; identifier où chaque exigence sera prouvée.

**Condition de passage :** attentes explicites, historique conservé, cible d’entraînement et contrainte de coût identifiées. Anticiper dès maintenant la cible cloud pour éviter un blocage final.

**État :** guide créé ; entraînement sur Kaggle privé gratuit confirmé ; remise à 15 h Paris / 17 h Tbilissi.

## 1 — Reprendre le corpus correctement

**Travail :** inventorier MediQAl, FrenchMedMCQA, MedQuAD et UltraMedical-Preference : URL réellement utilisée, version, licence, format source, langue, effectifs et éventuelles différences entre source originale et reconditionnement.

Examiner les convertisseurs et des exemples source → résultat pour chaque famille : toutes les propositions QCM, réponse complète, pas de métadonnée médicale inventée. Documenter les informations absentes. Vérifier le masquage FR/EN sans retirer les éléments médicaux utiles ; la détection d’identifiants seule n’est pas une certification RGPD.

Constituer environ 5 000 paires SFT bilingues ; justifier les exclusions plutôt que remplir artificiellement. Préparer les paires DPO de la source demandée avec justification chosen/rejected et statut réel de revue. L’anglais seul dans UltraMedical n’est pas une erreur de source ; il limite ce que cet alignement peut prouver sur le français.

**À produire :** JSONL/HF prêt à charger, data card, schéma, comptages par source/langue/split, journal des transformations, hashes et revue d’échantillons. Évaluer explicitement la couverture des comportements de triage ; une QA médicale n’a pas automatiquement un label de priorité.

**Condition de passage :** aucun choix QCM perdu ni texte coupé silencieusement ; provenance retrouvable ; groupes séparés entre train/validation/test ; labels et statuts honnêtes ; exemples contrôlés avant/après préparation. Toute revue clinique manquante reste un écart visible.

**Point de départ :** [manifeste corrigé](data/manifests/derived-source-medical-qa-sft-v2.1-reviewed.json), [audit des corrections](docs/evidence/PIPELINE_AUDIT_2026-09-05.md), [audit de fidélité](docs/evidence/SFT_V2_READINESS_2026-09-11.md). Ces preuves portent sur leur version, pas automatiquement sur un futur corpus.

**État au 16 septembre :** inventaire et intégrité du candidat SFT v2.1 repris dans la [fiche active](docs/technical/CORPUS_ETAPE_1_V1.md) et la [preuve datée](docs/evidence/AUDIT_CORPUS_ETAPE_1_2026-09-16.md). Le schéma de métadonnées et le processus RGPD sont documentés. La [consolidation DPO v2](docs/evidence/DPO_PROJECT_REVIEW_V2_2026-09-16.md) est terminée sans modifier les textes d'entraînement. Étape partiellement terminée : la revue contextuelle PII et le manifeste final restent ouverts. L'absence d'un référent clinique réel est documentée comme limite de transposition, pas comme blocage de la mission.

## 2 — Fixer l’évaluation et la baseline

**Travail :** figer les métriques et le protocole avant apprentissage. QA : exactitude lorsque la référence le permet, complétude, répétitions, arrêt et loss séparément. Triage : matrice des trois priorités, cas critiques, sous/sur-triage, faits inventés, recommandations dangereuses, qualité des questions et explications, FR/EN. Mesurer API : erreurs, latence p50/p95, débit et rapprochement des audits.

Les scénarios couvrent douleur thoracique, respiration, neurologie, pédiatrie, grossesse, vulnérabilité, informations insuffisantes et contradictions. Distinguer références proposées et validées ; ne pas créer de seuil clinique pour rendre un test vert.

**À produire :** protocole versionné et résultats de la Base avec prompts, limites de génération, backend et précision enregistrés. Préparer tôt un parcours complet de démonstration, avec inconnues explicites.

**Condition de passage :** on sait ce qui est mesuré, sur quelles données, et comment la même comparaison sera rejouée après SFT et DPO.

## 3 — SFT/LoRA sur GPU externe

**Travail :** garder Qwen3-1.7B-Base, vérifier la révision exacte et le template. Réutiliser une recette officielle compatible avec le runtime retenu, épingler les versions ; vérifier les tokens supervisés, le masquage du prompt et le terminateur.

Faire un seul essai court de préparation : chargement, quelques étapes, sauvegarde, recharge et génération. Si échec technique, corriger sa cause ; si exécution correcte mais qualité faible, examiner données/validation plutôt que rallonger aveuglément.

**À produire :** configuration, seed, versions, métriques et checkpoints, tracking MLflow ou W&B à mettre en place conformément à la spécification. Les expériences historiques utilisent des logs natifs, pas une preuve de tracking MLflow/W&B.

**Condition de passage au SFT complet :** pipeline et recharge vérifiés, dataset de l’étape 1 identifié, comparaison de validation disponible et explication pédagogique fournie à Pierre. Estimation de durée à partir du débit observé. Après entraînement : comparer Base/SFT et retenir un checkpoint selon la validation, sans régler sur le test final.

## 4 — DPO à partir du SFT retenu

**Travail :** vérifier le modèle initial, la référence, chosen/rejected, langues, longueurs et justifications de préférence. Réutiliser UltraMedical-Preference ; ne pas attribuer une validation clinique à une simple préférence de source.

**À produire :** configuration DPO, logs et poids, comparaison Base/SFT/DPO sur le même protocole. Séparer métriques internes de préférence et résultats de triage.

**Condition de passage :** apprentissage/recharge prouvés, résultats analysés, bénéfices et régressions explicites. Un DPO sans gain est un résultat à expliquer, pas un score à embellir. La durée de l’ancien essai n’est pas une cause démontrée de son faible effet.

## 5 — Démonstration cloud et CI/CD

**Travail :** FastAPI + vLLM + Docker ; questionnaire adaptatif ; schémas, anonymisation et garde-fous ; accès restreint ; audit avec versions. Reprendre les composants existants après contrôles ciblés.

**À produire :** endpoint réellement joignable depuis l’extérieur sur une cible autorisée, GitHub Actions avec tests ET déploiement, smoke test distant, démonstration multi-échanges FR/EN, mesures de latence/robustesse/audit et procédure d’arrêt.

**Condition de passage :** parcours réel observé, URL et accès transmissibles au jury, trace retrouvable. Un notebook Kaggle avec API sur localhost n’est pas ce livrable. Une CI de tests/build n’est pas une CD.

## 6 — Assembler la première livraison et préparer l’oral

| Livrable officiel | Contenu à remettre |
|---|---|
| Dataset médical bilingue versionné | JSONL/HF, data card, provenance/licences, splits, transformations et version du dépôt |
| Modèle SFT/LoRA puis DPO | Poids/adaptateurs avec base exacte, tokenizer, configurations, procédure de chargement et métriques |
| Endpoint cloud vLLM | URL accessible, mode d’accès autorisé et procédure de démonstration |
| CI/CD GitHub Actions | Dépôt, workflow de déploiement et preuve d’exécution |
| Rapport PDF ≤20 pages | Méthode, mesures, analyse, limites et roadmap |
| PowerPoint demandé par Pierre | Support pédagogique, démonstration et notes orales, chiffres cohérents avec le rapport |

ZIP : `Titre_du_projet_nom_prenom`. Fichiers : `Nom_Prenom_numero_nom_livrable_mmaaaa`, où `mmaaaa` est le mois de démarrage. Confirmer le nom de famille et le mois avant nommage final ; ne pas les déduire du compte GitHub.

Soutenance : 15 minutes de présentation, démonstration comprise ; tolérance 10–20 minutes. Puis 10 minutes de discussion et 5 minutes de débrief. Préparer méthode/validation, fine-tuning/optimisation, passage à l’échelle et déploiement.

La première version peut être identifiée comme brouillon avec écarts explicites ; ne pas la déclarer complète si endpoint, poids, données ou preuves manquent. Les poids et données ne vont pas dans le dépôt Git public par simple commodité.

## Plan jusqu’à demain

1. Maintenant : ranger la documentation et reprendre l’inventaire/revue du corpus ; arrêter les expériences parallèles non nécessaires.
2. Ensuite : choisir l’environnement externe autorisé, faire l’essai court et mesurer le débit. Fixer alors la durée réaliste du SFT/DPO et réserver du temps pour leur évaluation.
3. En parallèle du calcul : préparer endpoint/CD, rapport et dossier de livraison à partir des preuves existantes, sans annoncer les résultats futurs.
4. Avant la remise : figer les artefacts, vérifier leur ouverture et leurs liens, dérouler la démo et chronométrer l’oral. Éviter une nouvelle expérience de dernière minute qui empêcherait d’évaluer le modèle livré.

**Prochaine action concrète : étape 1, inventaire et revue des transformations.** Aucun nouvel entraînement n’est lancé par la création de ce guide.
