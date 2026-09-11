# Historique du projet — étapes, décisions et preuves au 11 septembre 2026

- **Date :** 2026-09-11
- **Statut :** draft — synthèse historique ; pilote v19, recharge/comparaison v20 et diagnostic de mémorisation v21 terminés
- **Périmètre :** du cadrage aux vérifications du corpus corrigé et aux résultats du pilote borné et à sa recharge vérifiée.
- **Sources :** cadrage et spécification, ADR-001 à ADR-012, preuves et notes pédagogiques liées dans chaque étape. Les statuts historiques sont datés et ne remplacent pas les résultats ultérieurs.

## 1. La mission et ce que nous devons réellement livrer

Le mandat demande un POC d'assistance au triage initial : collecte des symptômes, priorité parmi `maximum`, `moderate`, `deferred`, explication, garde-fous et traçabilité. Il prévoit une adaptation de Qwen3-1.7B-Base par SFT/LoRA, puis DPO, une API avec inférence, un conteneur, une chaîne CI/CD et un rapport technique de 20 pages maximum.

Le projet reste pédagogique. Le modèle ne remplace pas un professionnel et aucune performance clinique n'est validée. Une réussite de code, d'entraînement ou d'API constitue une preuve d'ingénierie avec un périmètre précis.

Sources : [cadrage](../../CADRAGE_MISSION.md), [spécification](../../SPEC_POC_TRIAGE_MEDICAL.md).

## 2. Comprendre les différentes « versions »

| Nom rencontré | Ce que ce nom désigne | Place dans le projet |
|---|---|---|
| Base | Qwen3-1.7B-Base, sans adaptation médicale du projet | Point de départ et comparaison |
| File de rédaction v1/v2 | Candidats documentaires pour rédiger des scénarios | Ce n'est pas un dataset SFT approuvé |
| SFT synthétique expérimental v1 | 5 000 scénarios produits selon un protocole proposé | Fixture pédagogique, pas le corpus du SFT Kaggle v5 |
| Corpus source SFT v1 | 5 000 QA tirées des trois sources | Utilisé par le premier SFT complet |
| Kaggle v5 / ancien SFT | Première exécution complète de 1 000 étapes | Réussite technique, défauts de génération mesurés ensuite |
| Kaggle v8 à v14 | Comparaisons, diagnostics et audit de labels | Majoritairement sans entraînement |
| Corpus source v2 | QCM complets et exemples trop longs exclus | Correction des transformations de v1 |
| Kaggle v15 à v17 | Trois continuations de 20 étapes depuis les poids v5 | Tests de mécanique et hypothèse de loss ; pas des SFT complets |
| Corpus v2.1 puis v2.1-reviewed | Isolation documentaire puis exclusion de 3 QCM ambigus | 4 700 lignes retenues pour le pilote |
| Kaggle v18 | Pilote borné depuis la base, sur les données revues | Baseline sauvegardée ; erreur FP16 au démarrage de l’optimisation |

Un numéro de notebook n'est donc ni un nombre d'epochs ni une version du corpus. Cette distinction explique une grande partie de la confusion accumulée.

## 3. Les étapes, dans l'ordre

### 28 août — gouvernance, schéma et premiers contrôles de données

**Question :** peut-on utiliser les sources de la mission sans perdre leur provenance, leurs restrictions et l'indépendance des évaluations ?

Nous avons créé les manifestes de sources, les schémas canoniques, les statuts d'anonymisation et de revue, ainsi que les règles de classement de la documentation. FrenchMedMCQA a été acquis à une version figée. Les recouvrements de questions entre ses splits ont conduit à une reconstruction contrôlée.

**Ce qui a changé dans notre approche :** nous n'avons pas traité « dataset téléchargé » comme synonyme de « dataset prêt à entraîner ». La reconstruction FrenchMedMCQA utilise des splits propres au projet ; elle ne permet pas de revendiquer un résultat sur le test original du benchmark.

Sources : [ADR-001](../decisions/ADR-001-ingestion-conditionnelle-des-sources.md), [contrat de données](CONTRAT_DONNEES_V1.md), [acquisition FrenchMedMCQA](../evidence/ACQUISITION_FRENCHMEDMCQA_2026-08-28.md), [reconstruction](../evidence/RECONSTRUCTION_FRENCHMEDMCQA_2026-08-28.md).

### Fondations — anonymisation, contrats API, scénarios et Docker

Nous avons construit des contrôles de schéma, une anonymisation Presidio/spaCy, des scénarios synthétiques, le contrat `POST /v1/triage`, des journaux minimisant les données et les bases Docker/CI.

**Limite essentielle :** valider un contrat JSON ou un transport simulé ne prouve pas que le vrai modèle produit une réponse pertinente. La même séparation vaut pour un conteneur construit et un endpoint réellement exposé.

Sources : [anonymisation](ANONYMISATION_V1.md), [preuve locale](../evidence/ANONYMISATION_V1_LOCAL.md), [contrats](VALIDATION_CONTRATS_V1.md), [API](API_POC_V1.md), [Docker/CI](REPRODUCTIBILITE_DOCKER_CI.md).

### 30–31 août — vérifier l'inférence et établir une baseline locale

Nous avons préparé des expériences synthétiques isolées et exécuté Qwen3 Base localement avec MLX sur Mac. Sur huit scénarios de triage synthétiques, **0/8 sorties respectaient le contrat JSON**. Certaines productions étaient répétitives ou commentées comme du code.

**Ce que cela prouve :** le modèle se charge et peut être évalué ; le contrat demandé n'est pas spontanément respecté dans cette configuration. Cela ne constitue ni un score clinique ni une preuve qu'un SFT corrigera tout.

Sources : [ADR-002](../decisions/ADR-002-micro-run-sft-synthetique-isole.md), [inférence locale](../evidence/UNSLOTH_LOCAL_INFERENCE_2026-08-30.md), [baseline mesurée](../evidence/BASELINE_QWEN3_BASE_2026-08-31.md).

### 31 août — audit du sens des sources et préparation DPO

MedQuAD contient des QA médicales, mais pas des priorités de triage. Les sous-ensembles dont les réponses ont été retirées par les auteurs ont été exclus. L'audit initial portait aussi sur MEDIQA 2019, puis cette interprétation de la source a été corrigée.

UltraMedical-Preference contient des préférences biomédicales. L'audit a révélé des prompts communs entre splits et des répétitions de prompts. Un index de reconstruction a été produit sans recopier les textes : **95 350 lignes train candidates, 2 227 validations candidates et 777 tests réservés**. Ces nombres décrivent une préparation, pas un entraînement DPO ni des préférences cliniquement approuvées.

**Décision :** une réponse de QCM ne doit pas devenir automatiquement un niveau d'urgence ; une préférence biomédicale ne garantit pas une préférence de prudence en triage.

Sources : [ADR-003](../decisions/ADR-003-medquad-source-de-connaissance.md), [audit UltraMedical](../evidence/ACQUISITION_AUDIT_ULTRAMEDICAL_PREFERENCE_2026-08-31.md), [ADR-005](../decisions/ADR-005-reconstruire-les-splits-dpo-ultramedical.md).

### 3 septembre — correction de la source MediQAl et clarification pédagogique

La source voulue était **ANR-MALADES/MediQAl**, francophone, et non **abachaa/MEDIQA2019**, corpus différent. Nous avons conservé l'historique et reconstruit la file de candidats avec la bonne source, en excluant les tests et les recouvrements identifiés.

Le projet scolaire ne disposant pas de référent clinique, ADR-007 a distingué **autorisation d'expérimenter** et **validation médicale**. Cela permet d'avancer techniquement sans attribuer de faux statuts d'approbation clinique.

Sources : [ADR-006](../decisions/ADR-006-remplacer-mediqa2019-par-mediqal.md), [file corrigée](../evidence/GENERATION_FILE_SFT_5000_V2_2026-09-03.md), [ADR-007](../decisions/ADR-007-autoriser-entrainement-pedagogique-non-clinique.md).

### 3–4 septembre — distinguer scénarios synthétiques et corpus source réel

Un générateur a produit 5 000 exemples synthétiques protocolisés. Les contrôles ont successivement détecté 168 puis 4 doublons ; ces sorties ont été refusées, jusqu'à obtenir zéro doublon exact dans le lot final. Cela validait la génération et les schémas, pas la qualité médicale ou la diversité sémantique.

Nous avons ensuite choisi un SFT de **QA réellement fournies par les sources** : 2 500 MedQuAD, 1 500 MediQAl et 1 000 FrenchMedMCQA, avec 4 000 train / 500 validation / 500 test. Le synthétique reste une fixture séparée.

**Raison :** adapter le domaine et le format de réponse avec du contenu traçable, tout en conservant l'évaluation de triage comme tâche distincte.

Sources : [génération synthétique](../evidence/GENERATION_SFT_EXPERIMENTAL_5000_2026-09-03.md), [ADR-008](../decisions/ADR-008-separer-sft-medical-et-dpo-triage.md), [génération source](../evidence/GENERATION_SFT_SOURCE_5000_2026-09-04.md).

### 4 septembre — passage du Mac à Kaggle et premier SFT complet

Le micro-run source local avait demandé environ 98 minutes pour 20 étapes. Kaggle privé, avec un seul T4 utilisé par le processus, a été retenu pour le calcul CUDA gratuit.

Le notebook **v5 a terminé 1 000 étapes, soit deux epochs**, sur le corpus source v1. Temps total Kaggle : environ **3 h 41** ; temps d'entraînement rapporté : **3 h 27 min 44 s**. L'archive et les adaptateurs ont été téléchargés et vérifiés. La meilleure loss de validation enregistrée par ce trainer était **1,2815**.

**Conclusion à ce stade :** entraînement terminé et artefacts conservés. La qualité des générations restait à démontrer ; une courbe de loss descendante ne suffisait pas.

Sources : [micro-run source](../evidence/SFT_SOURCE_MICRO_RUN_2026-09-04.md), [ADR-009](../decisions/ADR-009-utiliser-kaggle-pour-le-sft-complet.md), [résultat v5](../evidence/SFT_KAGGLE_FULL_RUN_2026-09-04.md).

### 5 septembre — première comparaison et découverte des répétitions

La comparaison v8 a évalué Base et SFT sur les mêmes 500 validations. La loss de réponse pondérée par les tokens a baissé de **2,10444 à 1,52624**. Mais **30/30 générations SFT atteignaient le plafond de 256 tokens**, avec répétitions, contre 15/30 pour la base.

**Décision :** suspendre le passage DPO et diagnostiquer les générations. Cette décision ne signifiait pas que tout l'entraînement était inutile : elle distinguait un gain de vraisemblance des références d'un comportement de génération encore défectueux.

Attention : la loss de réponse 1,52624 ne se compare pas directement à la `eval_loss` 1,2815 du run initial ; le périmètre de tokens et l'agrégation diffèrent.

Source : [comparaison et diagnostics](../evidence/BASE_SFT_KAGGLE_2026-09-05.md).

### 5 septembre — incidents Kaggle et élimination progressive d'hypothèses

Les versions de préparation ont rencontré des attachements absents ou ambigus. Kaggle résolvait parfois la dernière sortie du notebook au lieu des poids v5. Un petit dataset **privé d'adaptateur v5**, créé après autorisation, a stabilisé cette entrée ; les poids sont sélectionnés par empreinte.

Les diagnostics ont ensuite testé :

| Hypothèse | Expérience | Observation et conclusion limitée |
|---|---|---|
| Le critère d'arrêt suffit à corriger | v10, EOS et fin de message acceptés | 3/3 sorties plafonnent sans ces tokens : réglage d'arrêt insuffisant |
| La quantification explique seule le défaut | v11, NF4 puis FP16 | Répétitions dans les deux cas : aucun chargement testé ne résout le problème |
| Le backend Transformers est seul responsable | v13, backend Unsloth original | Défaut toujours présent sur les trois diagnostics |
| Le modèle apprend réellement l'EOS attendu | v14, inspection des labels, zéro entraînement | Aucun EOS natif supervisé avec le format initial ; un EOS par exemple avec le candidat corrigé |

La v12 avait échoué sur un placement multi-GPU ; le diagnostic suivant a imposé un seul GPU. Ces erreurs d'infrastructure sont distinctes des erreurs de données et des défauts de réponse. Aucune cause unique de tous les défauts n'a été démontrée.

Sources : [diagnostics](../evidence/BASE_SFT_KAGGLE_2026-09-05.md), [audit pipeline](../evidence/PIPELINE_AUDIT_2026-09-05.md), [labels v14](../evidence/SFT_LABEL_AUDIT_V14.json).

### 5–11 septembre — correction du corpus et du terminateur

L'audit des transformations a découvert des QCM privés de leurs choix et des textes tronqués. Le corpus **v2** a restauré les choix et exclu les exemples trop longs, en conservant les splits des identifiants retenus : 4 899 anciens identifiants conservés et 101 remplacements.

Le format candidat termine la dernière réponse avec l'EOS natif. Les prompts et le vocabulaire restent contrôlés. Les embeddings de certains marqueurs de conversation étaient identiques et figés ; cela a motivé l'inspection, sans constituer une preuve de cause unique.

Sources : [ADR-011](../decisions/ADR-011-verifier-pipeline-avant-entrainement.md), [audit](../evidence/PIPELINE_AUDIT_2026-09-05.md), [révision des données](../evidence/SFT_V2_REVISION_CHECK.json).

### 11 septembre — trois micro-runs, puis correction de notre interprétation

Les v15–v17 reprennent toutes **les poids v5**, sur 64 exemples train et trois validations, pendant 20 étapes. Elles ne sont pas un SFT corrigé complet depuis la base.

| Version | Changement testé | Observation |
|---|---|---|
| v15 | Corpus v1 + EOS natif | 3/3 sorties terminent ; recharge identique ; contenu parfois hors sujet |
| v16 | Corpus v2 + EOS, loss sur toute la conversation | 3/3 sorties terminent ; deux QCM divergent des références |
| v17 | Même point de départ et mêmes données, loss sur réponse seule | Masque réel validé ; 3/3 sorties terminent ; deux QCM encore divergents |

**Réflexion corrigée :** dire « deux QCM incorrects, donc la pipeline est encore cassée » aurait été excessif. Ces essais prouvaient surtout la mécanique. Ils étaient trop petits et partaient d'un ancien SFT défectueux pour décider de la qualité générale d'un futur modèle.

La proposition d'une relance complète a été remplacée, à la suite de l'objection du porteur du projet sur le risque de perdre quatre heures, par **un pilote représentatif et borné**. L'objectif est d'obtenir un signal avant d'investir davantage.

Source : [micro-runs et leurs limites](../evidence/SFT_MICRO_RUNS_2026-09-11.md).

### 11 septembre — audit élargi avant pilote

Le contrôle suivant a été étendu aux sources, à l'isolation documentaire et au vrai collateur TRL. Il a trouvé des groupes documentaires communs entre splits : **297 lignes exclues**, puis **3 QCM supplémentaires** écartés pour choix dupliqués dans la source.

Le corpus revu contient **4 700 lignes : 3 721 train, 479 validation, 500 test strictement inchangés**. Les vérifications des 4 200 exemples de développement établissent la fidélité aux sources, les anonymisations expliquées, l'absence de troncature et la supervision de toute la réponse, EOS compris. Les 8 400 champs ont été rescannés selon la politique d'identifiants directs.

Une expérience CPU sur un modèle miniature synthétique a montré que **4 étapes continues donnent les mêmes poids que 2 étapes + interruption + reprise jusqu'à 4**. Cette preuve n'est pas encore une preuve de reprise CUDA avec quantification et scaler FP16.

Sources : [ADR-012](../decisions/ADR-012-isoler-les-groupes-et-borner-le-pilote-sft.md), [audit final complet](../evidence/SFT_V2_READINESS_2026-09-11.md).

### 11 septembre — lancement du pilote v18

Après présentation pédagogique des résultats et accord de continuation, le pilote a été envoyé dans le notebook Kaggle privé existant. La compression des conversations permet de tenir sous la limite de taille du notebook tout en reconstruisant les fichiers exactement, vérifiés par hash. Aucun nouveau dataset externe n'a été créé.

Le pilote repart de **la base avec un LoRA neuf**, utilise le corpus revu et s'arrête à **150 étapes ou 1 800 secondes de phase d'entraînement**. La préparation et les évaluations initiale/finale ont un coût supplémentaire. L'horizon du scheduler est fixé pour une éventuelle reprise, sans autoriser l'exécution complète de cet horizon.

La comparaison prévoit 479 mesures de loss et 30 générations fixes, dont 15 FR et 15 EN. Les logs GPU ont confirmé le contrôle des 4 200 labels. **Le pilote s’est ensuite arrêté avant la première étape optimiseur**, avec `ValueError: Attempting to unscale FP16 gradients.` La baseline a été sauvegardée, mais aucune comparaison après entraînement n’est disponible. Cette erreur de mécanique numérique ne mesure pas la qualité du corpus ; sa cause racine reste à vérifier. Voir le [constat v18](../evidence/SFT_V2_PILOT_V18_2026-09-11.md).

Sources : [configuration](../../configs/sft-v2.1-pilot.json), [preuve de lancement v18](../evidence/SFT_V2_PILOT_LAUNCH_2026-09-11.json).

### 11 septembre — correction FP16 et pilote v19 terminé

La cause v18 est localisée : le trainer Unsloth réactive la conversion FP16 d’évaluation, puis le scaler refuse les gradients des paramètres ainsi convertis. La correction conserve les paramètres LoRA en FP32 après construction du trainer. Un smoke GPU vérifie deux étapes, une recharge exacte et une reprise de l’optimiseur jusqu’à quatre étapes. Le pilote depuis la base termine ensuite 150 étapes, avec sauvegarde complète et empreintes vérifiées localement.

Sur 479 validations, la loss moyenne par exemple passe de 1,4569 à 0,7121. La revue des choix QCM donne 5/15 accords source pour Base et 7/15 à 150 étapes, avec quatre gains et deux régressions. Les réponses anglaises restent répétitives et parfois contradictoires avec leurs références.

Source : [résultat v19](../evidence/SFT_V19_PILOT_RESULT_2026-09-11.md).

### 11 septembre — v20, recharge et comparaison sans entraînement

Une nouvelle session GPU recharge le checkpoint 150 : les 30 générations sont identiques et la loss diffère de seulement 5,96 × 10⁻⁸. Les checkpoints 50 et 100 sont également évalués. Les terminaisons EOS sont respectivement 26/30, 25/30 et 22/30 aux étapes 50/100/150. Les accords de choix QCM sont 6/15, 5/15 et 7/15. Des réponses courtes aux étapes précoces se limitent à recopier la question : la terminaison seule ne suffit pas.

**Décision :** la mécanique testée est prouvée, mais aucun checkpoint n’est retenu comme modèle final satisfaisant. Aucun SFT long ou DPO supplémentaire n’est lancé. La prochaine expérience doit comparer une hypothèse explicite, avec validation figée et test toujours réservé.

Source : [bilan v20](../evidence/SFT_V20_CHECKPOINT_RESULT_2026-09-11.md).

### 11 septembre — v21, diagnostic de mémorisation réussi

Pour départager un défaut d’apprentissage et une difficulté de généralisation, un lot figé de douze exemples train (quatre par source, réponses courtes) est appris depuis la base. Après 300 étapes, soit 25 passages, les douze réponses sont reproduites textuellement et s’arrêtent par EOS. La loss sur ce lot passe de 1,15525 à 0,000078016.

**Réflexion corrigée :** les sources ne doivent pas être modifiées sur la seule hypothèse que leur style cause les répétitions. La pipeline est capable d’apprendre ce lot ; la suite porte sur la généralisation et l’exposition au corpus complet. Les hyperparamètres et la taille du lot diffèrent du pilote général, et ces poids diagnostiques ne deviennent pas un SFT final.

Source : [résultat v21](../evidence/SFT_MEMORIZATION_V21_RESULT_2026-09-11.md).

### 11 septembre — reprise générale v22 lancée

Après accord du porteur, reprise préparée depuis le checkpoint général v19 à 150 étapes, jusqu’à 500 étapes au total ou 30 minutes de phase entraînement. Corpus et scheduler inchangés ; les poids du diagnostic v21 sont exclus. Les contrôles locaux passent et Kaggle confirme `RUNNING`. La restauration GPU effective, la fin de l’entraînement et la comparaison qualitative ne sont pas encore observées.

Source : [protocole et preuve de lancement](SFT_CONTINUATION_150_500_2026-09-11.md).

## 4. Travaux parallèles : API, audit et préparation du DPO

L'API a évolué vers un contrat de fournisseur compatible vLLM, avec validation de schéma, traitement de réponses invalides/tronquées et audit minimisant les textes. Des tests locaux et un conteneur hors réseau ont permis de vérifier plusieurs comportements. Une tentative de téléchargement de suffixes publics par un composant d'anonymisation a été supprimée au profit de ressources embarquées.

Pour le DPO, un premier lot a été rejeté parce que le NER masquait des notions médicales comme des personnes ou des lieux. Un second lot de **512 paires train et 64 validations** a été préparé avec la politique d'identifiants directs. Il reste candidat : revue des préférences et de confidentialité à terminer, biais linguistique anglais et limites de sélection documentés.

**Ni DPO entraîné, ni modèle réel servi par vLLM, ni déploiement pilote ne sont prouvés à ce stade.**

Source : [preuve locale post-SFT](../evidence/POST_SFT_IMPLEMENTATION_2026-09-05.md).

## 5. Les enseignements qui structurent la suite

1. **Une source n'est pas une cible de triage.** Adapter des QA médicales et apprendre une politique d'escalade sont deux problèmes différents.
2. **La loss ne suffit pas.** Une référence plus probable peut coexister avec des générations répétitives ou fausses.
3. **La comparaison doit rester appariée.** Même corpus, prompt, terminaison, décodage et agrégation ; les chiffres de v1 et du corpus revu ne sont pas directement interchangeables.
4. **L'isolation doit dépasser l'identifiant de ligne.** Documents, vignettes et réponses communes peuvent rapprocher artificiellement train et évaluation.
5. **Le trainer réel est la dernière étape du contrôle des données.** Un JSON propre ne prouve pas que les labels entraînent les bons tokens.
6. **Une recharge de poids n'est pas une reprise d'entraînement.** L'optimiseur, le scheduler, les RNG et le scaler éventuel doivent aussi être conservés.
7. **Un micro-run répond à une question bornée.** Trois réponses n'autorisent pas une conclusion globale, favorable ou défavorable.
8. **Les résultats négatifs doivent être conservés.** Ils expliquent les décisions et empêchent de répéter les mêmes essais.
9. **La validation technique reste distincte de la validation clinique.** Aucune étape ne transforme automatiquement le POC en outil médical utilisable sur des patients.

## 6. Ce qui reste à faire, avec ses dépendances

| Étape | Action suivante | Condition avant de passer plus loin |
|---|---|---|
| Pilote terminé | Analyser les limites qualitatives persistantes | Correction FP16 et optimisation GPU prouvées par v19 |
| Recharge/reprise GPU | Conserver les preuves v19/v20 | Reprise courte observée ; checkpoint final rechargé avec 30 générations identiques |
| SFT prolongé | Décider si poursuivre le pilote ou ajuster | Signal qualitatif suffisant ; aucune prolongation automatique |
| DPO | Revoir et figer les préférences, faire un essai court | SFT de référence et données DPO admissibles |
| Comparaison finale | Base/SFT/DPO, robustesse et scénarios spécifiés | Protocole identique, test réservé pour l'évaluation finale |
| Inférence/API | Brancher le vrai modèle, mesurer latence et garde-fous | Preuve de bout en bout, distincte des mocks |
| Démonstration/CI-CD | Exposition pilote autorisée et tests réels | Cible, autorisation, déploiement et smoke vérifiés |
| Rapport final | Synthétiser les preuves dans 20 pages maximum | Résultats mesurés, limites et résultats négatifs inclus |

## 7. Comment utiliser cette documentation

Ce document est le fil chronologique professionnel. La [synthèse pédagogique](../learning/34-retour-sur-la-demarche-du-projet.md) explique les notions et les changements de raisonnement. Les documents `evidence/` sont les sources des chiffres ; les ADR consignent les décisions ; les scripts/configurations servent à reproduire les opérations. Le rapport final doit s'appuyer sur ces preuves, pas sur une note d'apprentissage ou un statut de lancement.
