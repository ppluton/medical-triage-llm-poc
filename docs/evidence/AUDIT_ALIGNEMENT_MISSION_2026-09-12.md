# Audit de réalignement avec la mission OpenClassrooms

- Date : 2026-09-12
- Statut : draft — constats documentaires et revue statique ; plan correctif proposé
- Périmètre : mission intégrale, étapes 0 à 3 dépliées, livrables et soutenance ; confrontation aux artefacts locaux à `29c7a68`.
- Environnement : navigateur intégré Codex, session OpenClassrooms de l'utilisateur ; dépôt `ppluton/medical-triage-llm-poc`, branche `codex/complete-poc-evaluation`.
- Sources externes : [mission](https://openclassrooms.com/fr/paths/2053/projects/3421/8585-mission---developpez-le-poc-d'un-agent-de-triage-medical), [livrables et soutenance](https://openclassrooms.com/fr/paths/2053/projects/3421/8586-livrables-et-soutenance), [catalogue Unsloth lié par l'école](https://unsloth.ai/docs/get-started/unsloth-notebooks).
- Sources internes : [cadrage](../../CADRAGE_MISSION.md), [spécification](../../SPEC_POC_TRIAGE_MEDICAL.md), [audit du premier SFT](PIPELINE_AUDIT_2026-09-05.md), [bilan v22](SFT_V22_RESULT_2026-09-12.md), [ADR-008](../decisions/ADR-008-separer-sft-medical-et-dpo-triage.md).

## Ce que demande effectivement l'école

La mission impose Qwen3-1.7B-Base, une spécialisation SFT avec LoRA, puis DPO sur UltraMedical-Preference. Elle propose environ 5 000 paires SFT bilingues, des sources médicales nommées, l'anonymisation, les métadonnées, la traçabilité et des jeux séparés. Les petits runs avant montée en charge sont explicitement recommandés.

Elle demande également une évaluation du triage et des réponses dangereuses, un endpoint cloud utilisant vLLM, FastAPI/Docker, GitHub Actions et un rapport PDF de vingt pages maximum. La soutenance comprend une démonstration, quinze minutes de présentation, dix minutes de discussion et cinq minutes de débrief.

Les étapes détaillées demandent réellement des préférences validées cliniquement et des métriques/seuils définis. Ce n'est pas une exigence entièrement inventée par notre spécification. En revanche, la page ne fixe aucun score QCM minimal ni l'obligation de corriger tous les QCM avant une expérience DPO. L'interprétation scolaire de la validation clinique reste à clarifier avec le mentor ; cet audit n'accorde aucune validation fictive.

Le lien « exemple de notebook » conduit à un catalogue Unsloth général, pas à une recette CHSA figée ni à un corpus corrigé prêt à entraîner. Aucun hyperparamètre précis n'est imposé dans les sections lues. Les contenus complets des cours, de l'article JAMA et de chaque documentation externe n'ont pas été audités ici.

## Écarts et erreurs établis

| Constat | Preuve et portée | Correction nécessaire |
|---|---|---|
| Préparation initiale défectueuse | Audit du 5 septembre : au moins un choix absent dans 2 249/2 250 QCM de développement, 101 réponses tronquées au total, absence d'EOS natif supervisé. Ces défauts appartiennent à notre transformation et au rendu, pas à une défaillance globale des sources. | Conserver les corrections v2.1 et les contrôles déjà effectués ; ne pas reconstruire encore le corpus sans nouveau défaut précis. |
| Évaluation trop éloignée du livrable | La comparaison v22 mesure loss sur 479 exemples et génération sur 30 QA, dont 15 QCM FR. Elle ne mesure pas directement le questionnaire adaptatif ni les trois niveaux de triage. | Séparer comparaison QA et évaluation du parcours de triage ; publier les deux avec leurs limites. |
| Porte de passage trop contraignante et mal définie | La roadmap exige « SFT meilleur et sans régression de sûreté » avant DPO ; le suivi s'est concentré sur de minuscules diagnostics QA sans seuil scolaire correspondant. | Retenir un SFT expérimental reproductible avec ses défauts documentés ; décider d'un DPO borné sur critères techniques et protocole explicite, sans promettre un gain. |
| Promesse excessive sur DPO | ADR-008 résume DPO en préférences de prudence. Le préparateur décrit pourtant ses paires comme des préférences biomédicales, non validées pour le triage. | Vérifier la signification des préférences et mesurer leur effet réel ; ne pas promettre qu'elles apprendront automatiquement le triage. |
| Chaîne DPO encore attachée à l'ancien SFT | `configs/dpo.yaml` nomme v5 ; `scripts/run_dpo.py` et `load_dpo_handoff` exigent le hash `3f050ae…`, alors que l'adaptateur 500 vaut `5c195a8…`. Revue statique : le garde de hash rejetterait le checkpoint actuel. | Remplacer cette dépendance historique par un contrat explicite du SFT retenu, tokenizer et comparaison associés ; vérifier ensuite une exécution courte. Ne pas supprimer les contrôles. |
| Documentation d'état contradictoire | La roadmap annonce v22 terminée puis conserve des jalons « pilote en cours » et des incréments anciens présentés comme actuels. | Une seule vue courante des cinq livrables ; déplacer les explications historiques vers l'historique. |
| Modèle réel jusqu'à l'API non démontré | Les preuves décrivent contrats, transport simulé et Docker ; elles distinguent explicitement l'inférence réelle vLLM manquante. | Faire une démonstration de bout en bout et mesurer latence/traçabilité ; les tests simulés ne closent pas ce livrable. |

## Sources : concordances et différences à ne pas confondre

MediQAl et UltraMedical correspondent aux identifiants liés par l'école. Pour FrenchMedMCQA et MedQuAD, la page expose deux liens mal formés : `http://nthngdy/frenchmedmcqa` et `http://keivalya/MedQuad-MedicalQnADataset`. Nos manifestes utilisent `qanastek/frenchmedmcqa` et l'amont `abachaa/MedQuAD`. Les familles de corpus concordent, mais l'équivalence des versions et des transformations avec ces reconditionnements n'est pas établie par cet audit. Ce point mérite une comparaison de provenance ciblée, pas une accusation de « mauvais corpus » ni un remplacement automatique.

Les 4 700 lignes actuelles comprennent 3 721 train, 479 validation et 500 test. L'école donne une cible approximative dans l'étape détaillée et privilégie la qualité sur la quantité. L'écart doit être expliqué ; il ne justifie pas à lui seul de réentraîner.

## Ce qui reste utile et ce qui n'est pas prouvé

- Prouvé par les archives relues : entraînement général jusqu'à 500 étapes, baisse de loss, checkpoints sauvegardés ; corrections de préparation documentées.
- Mesuré sur le petit lot : Base 5/15 accords QCM, SFT 500 6/15 ; EOS 20/30 puis 26/30. Aucun gain général de justesse n'en découle.
- Non prouvé : cause unique des erreurs résiduelles, maîtrise du triage, bénéfice DPO, intégration du modèle actuel à vLLM/API.
- Le diagnostic de mémorisation 12/12 valide un cas borné ; il ne certifie pas tous les formats et toutes les conditions d'inférence.
- Nous ne disposons d'aucune preuve sur les configurations, résultats ou critères appliqués aux autres étudiants.

## Plan de réalignement proposé

1. **Figer l'état utile** : conserver corpus revu, Base et checkpoints généraux. Aucun nouveau SFT long pendant cet audit. Donner aux cinq livrables une checklist unique, sans effacer les résultats négatifs.
2. **Terminer une évaluation bornée pertinente** : vérifier la recharge du SFT retenu, comparer Base/SFT sur validation QA avec scores adaptés, puis sur des scénarios de triage séparés couvrant FR/EN, urgence, incertitude et questions complémentaires. Distinguer la sortie brute des corrections des garde-fous. Les références synthétiques restent proposées ; ne pas ouvrir le test pour régler le modèle. Un protocole, un budget et une décision à son terme, sans nouvelle série indéfinie de diagnostics.
3. **Raccorder et expérimenter DPO** : corriger le contrat v5 obsolète, revoir le lot UltraMedical et ses contrôles de confidentialité, vérifier une petite exécution depuis le SFT courant avec référence gelée. Une comparaison peut être négative ; elle doit rester exploitable pour le rapport. Clarifier avec le mentor la preuve attendue pour la validation clinique des préférences, sans présenter une revue automatique comme clinique.
4. **Fermer la chaîne de démonstration** : vrai modèle, vLLM, API, audit et mesures ; définir la cible cloud et ses contraintes avant publication. L'autorisation Kaggle gratuite ne vaut pas autorisation d'un hébergement payant.
5. **Comparer Base/SFT/DPO et livrer** : protocole commun, test final réservé après gel des choix, limites, PDF ≤20 pages, artefacts et démonstration. Aucune garantie de réussite à la soutenance ni de qualité clinique n'est déduite de la seule exécution.

## Méthode de vérification

Lecture par navigateur Codex du texte de `main`, dépliage des quatre étapes, lecture de la page de soutenance et inspection des liens de ressources. Relecture locale des manifestes, preuves et conditions de chargement DPO. Aucun entraînement, aucune modification de code exécutable, aucune publication ; audit statique et documentaire seulement. Le cadrage et la spécification restent inchangés.
