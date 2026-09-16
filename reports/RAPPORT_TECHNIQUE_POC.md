# Rapport technique — POC d'assistance au triage médical CHSA

- **Date :** 2026-09-16
- **Statut :** draft — rapport intermédiaire, livrables incomplets
- **Sources :** [cadrage](../CADRAGE_MISSION.md), [spécification](../SPEC_POC_TRIAGE_MEDICAL.md), [audit de mission](../docs/evidence/AUDIT_ALIGNEMENT_MISSION_2026-09-12.md) et preuves liées ci-dessous.
- **Format final :** PDF de vingt pages maximum ; ce document Markdown n'est pas encore le PDF final.

## 1. Objectif et état du POC

Le CHSA souhaite un assistant de triage initial qui recueille les symptômes, demande les informations utiles, propose l'un des niveaux `maximum`, `moderate` ou `deferred`, explique sa proposition et conserve une trace exploitable. Ce projet d'étude doit démontrer une faisabilité technique ; il ne constitue pas un outil de diagnostic, de prescription ou de décision clinique autonome.

La chaîne actuelle comprend un corpus bilingue v2.2 finalisé par des contrôles techniques de confidentialité, un nouveau pilote SFT de Qwen3-1.7B-Base à 150 étapes et une lignée DPO réancrée sur ce corpus. Le pilote v39 réduit la NLL validation de 1,4569 à 0,7118 et produit un checkpoint complet ; sa recharge principale est encore vérifiée par la v40 en lecture seule. L’intégration historique vLLM/API est démontrée par v37 sur GPU T4 en accès local privé. La revue aveugle commune signale 7/17 sorties Base, 6/17 SFT et 6/17 DPO ; aucun bénéfice DPO n’est démontré. Les garde-fous évitent un délai dangereux dans ce lot, mais corrigent encore la majorité des sorties. Aucun gain de pertinence clinique ni déploiement hospitalier n'est établi.

| Livrable demandé | Preuve disponible | Écart restant |
|---|---|---|
| Dataset bilingue documenté | SFT v2.2 : 4 700 lignes, 31 masques sur 22 lignes, zéro identifiant direct au rescan | Publication externe, certification RGPD et validation clinique absentes |
| SFT puis DPO comparés | SFT v39 exécuté ; baseline Base/SFT/DPO v37 et résultat négatif DPO documentés | Recharge v40, nouveau DPO depuis v39 et ouverture unique de la réserve |
| Endpoint cloud vLLM/API | Intégration réelle v37, audit, dialogues et garde-fous mesurés | Déployer et tester sur une cible extérieure autorisée |
| GitHub Actions tests/déploiement | 215 tests ; image et factory privée vérifiées localement | Exécution GitHub distante vérifiée et déploiement automatisé |
| Rapport et soutenance | Présente synthèse et preuves intermédiaires | Mesures finales, PDF ≤20 pages et démonstration |

## 2. Données et gouvernance

Les sources retenues sont MediQAl, FrenchMedMCQA et MedQuAD pour le SFT, et UltraMedical-Preference pour le DPO. La provenance, les licences et les transformations sont décrites dans les manifestes et documents de gouvernance. Les liens de l'école vers FrenchMedMCQA et MedQuAD sont mal formés ; les familles de sources correspondent, mais l'équivalence exacte des reconditionnements n'est pas établie par l'audit. Les données brutes et les poids restent hors Git.

Le premier corpus comptait 5 000 lignes. Notre transformation perdait des propositions QCM dans 2 249 des 2 250 QCM de développement, tronquait 101 réponses et n'enseignait pas correctement l'arrêt natif de la réponse. Ces erreurs relèvent de notre préparation, pas d'une défaillance démontrée des sources. Les corrections, exclusions et masquages documentés conduisent au corpus v2.2 :

| Split | Lignes | Usage |
|---|---:|---|
| Train | 3 721 | Optimisation SFT |
| Validation | 479 | Suivi, comparaison et choix de développement |
| Test | 500 | Évaluation finale réservée ; non utilisée pour régler le modèle |

Les choix et réponses complets, le masquage du prompt et la présence d'un EOS supervisé ont été contrôlés sur les 4 200 exemples de développement. Une revue technique a ensuite masqué 31 occurrences `PATIENT_NAME` sur 22 lignes ; le rescan des 9 400 champs ne trouve plus d'identifiant direct. Les détections contextuelles de personnes, lieux et dates ont été conservées sous la politique des sources publiques afin de ne pas corrompre le contenu médical. Cette décision ne constitue ni une anonymisation exhaustive ni une certification RGPD. Le corpus reste bilingue, sans imposer l'égalité du nombre de tokens français et anglais. Les réponses MedQuAD sont souvent longues ; l'équilibre des lignes ne garantit donc pas l'équilibre des tokens. La cible scolaire est d'environ 5 000 paires, avec priorité à la qualité.

Les réponses QA sources ne sont pas des annotations de priorité de triage. Les scans d'identifiants et la revue technique ne sont pas une validation clinique ni une preuve d'anonymisation exhaustive. Les scénarios de démonstration sont synthétiques et leurs références portent le statut `proposed_educational_only`.

Preuves : [audit de pipeline](../docs/evidence/PIPELINE_AUDIT_2026-09-05.md), [finalisation de confidentialité](../docs/evidence/SFT_PRIVACY_FINALIZATION_2026-09-16.md), [manifeste SFT v2.2](../data/manifests/derived-source-medical-qa-sft-v2.2-privacy-finalized.json) et [lignée DPO v3](../docs/evidence/DPO_V22_LINEAGE_REBIND_2026-09-16.md).

## 3. Méthode et entraînements SFT

La base est `unsloth/Qwen3-1.7B-Base`, révision `e249956c10337100486d07afb77e3eb2b30906b8`. La recette corrigée utilise le chargement 4 bits, LoRA de rang et alpha 16, batch effectif 8, contexte de 2 048 tokens, learning rate initial `1e-4` et seed 42. La loss supervise uniquement la réponse et son EOS. Le calcul utilise FP16 AMP, avec paramètres entraînables LoRA maintenus en FP32. Les versions CUDA et bibliothèques sont consignées dans la configuration du run.

L'entraînement historique v5 du 4 septembre a exécuté 1 000 étapes sur le premier corpus. Son exécution technique a abouti, mais ses répétitions et les défauts de préparation empêchent d'en faire la référence courante. Les résultats historiques restent archivés ; ils ne sont pas directement comparables aux pertes recalculées avec un corpus et une agrégation différents.

Le SFT corrigé a progressé jusqu'à 150 puis 500 étapes. La continuation v22 a restauré optimiseur, scheduler, scaler et RNG ; elle a ajouté 350 étapes en environ 26 min 41 s, évaluations périodiques incluses. Le checkpoint atteint environ 1,073 époque. Ses fichiers ont été archivés et leurs empreintes contrôlées. Le diagnostic distinct de mémorisation sur douze exemples ne sert pas de modèle général ni de point de départ au DPO.

L'adaptateur SFT 500 a pour SHA-256 `5c195a8c83bfd6493e7ffd74ec20e3d97207f9b650850aabd8de25afffea626d`. Une archive correcte ne prouve pas à elle seule que l'inférence dans un nouveau processus reproduit les sorties.

Afin que les poids livrés correspondent au corpus final, la v39 redémarre depuis la Base exacte et entraîne 150 étapes sur v2.2. Son adaptateur porte le SHA-256 `c911f9c631be825f4af5c7dff5a87409d1ee91d4c28e2b0b1571e808e055d413`. Les 392 tenseurs LoRA sont finis et modifiés ; la NLL validation atteint 0,711802. Huit générations sur trente atteignent encore le plafond, toutes sur MedQuAD. La recharge du checkpoint principal reste la porte v40 avant admission comme référence DPO.

Preuves : [SFT historique](../docs/evidence/SFT_KAGGLE_FULL_RUN_2026-09-04.md), [résultat v22](../docs/evidence/SFT_V22_RESULT_2026-09-12.md), [pilote final v39](../docs/evidence/SFT_V39_RESULT_2026-09-16.md).

## 4. Évaluation Base/SFT et résultats négatifs

La comparaison courante utilise les mêmes 479 exemples de validation pour la loss et les mêmes trente prompts pour les générations, en décodage greedy avec plafond de 512 tokens. La loss ci-dessous est une moyenne par exemple ; elle ne doit pas être confondue avec l'ancienne agrégation pondérée par token. Quinze des trente générations sont des QCM français. Ces lots sont des outils de développement, pas un test final indépendant.

| Mesure | Base | SFT 150 | SFT 500 |
|---|---:|---:|---:|
| Loss réponse moyenne par exemple, 479 validations | 1,456922 | 0,712133 | 0,673777 |
| Réponses terminées par EOS natif, sur 30 | 20 | 22 | 26 |
| Réponses atteignant le plafond, sur 30 | 10 | 8 | 4 |
| Accord exact des choix QCM, sur 15 | 5 | 7 | 6 |
| Fraction moyenne de 4-grammes répétés | 0,3447 | 0,2426 | 0,1525 |

La baisse de loss et l'amélioration des arrêts sont observées. Elles ne démontrent pas une amélioration générale de la justesse. Les quatre plafonds anglais du SFT 500 correspondent à de vraies répétitions ; d'autres réponses contredisent les références sources. Le petit lot QCM ne permet pas de conclure à une régression statistique générale entre 150 et 500 étapes.

La mission exige également d'évaluer le parcours de triage. Dix-huit scénarios de développement couvrent neuf familles en français et anglais : douleur thoracique, détresse respiratoire, déficit neurologique, pédiatrie, grossesse, vulnérabilité, informations insuffisantes, contradictions et cas stable. Le protocole distingue validité JSON, accord avec les références proposées, présence de questions complémentaires et sorties invalides. La présence d'une question ne prouve pas sa pertinence ; le questionnaire adaptatif au fil d'un échange reste à vérifier.

Les v23 et v24 ont échoué au contrôle de recharge. La [v25](../docs/evidence/TRIAGE_V25_RESULT_2026-09-12.md) confirme un cache Unsloth périmé : après invalidation, 30/30 générations sont reproduites. Sur 18 scénarios de triage, Base et SFT produisent respectivement 0 et 10 JSON conformes, et 0 et 4 priorités conformes aux références proposées. Le SFT réussit 2 des 6 cas critiques en comptant les sorties invalides comme échecs. La consigne omettait les définitions explicites des niveaux. La [v26 corrigée](../docs/evidence/TRIAGE_V26_RESULT_2026-09-12.md) donne 12/18 JSON conformes et 6/18 priorités conformes pour le SFT, contre 0/18 pour la Base. Le résultat sur les six cas critiques reste 2/6 ; des faits inventés persistent malgré une priorité parfois correcte. Ces résultats restent insuffisants et sans validation clinique.

Preuves : [mesures SFT](../docs/evidence/SFT_V22_RESULT_2026-09-12.md), [échec v23](../docs/evidence/TRIAGE_V23_LAUNCH_2026-09-12.md), [contrôle v24](../docs/evidence/TRIAGE_V24_LAUNCH_2026-09-12.md).

### Test final indépendant v35

Le protocole a été figé avant l'ouverture des 500 exemples de test. Les trois modèles ont été évalués sur les mêmes exemples et 50 générations sélectionnées par hash, en Transformers FP4 et décodage greedy. Les fichiers et les calculs ont été vérifiés après téléchargement ; aucune modification du modèle n'est déduite de ce test.

| Mesure finale | Base | SFT 500 | DPO |
|---|---:|---:|---:|
| Perte réponse moyenne par exemple, 500 tests | 1,575202 | 0,844017 | 0,842970 |
| Arrêts EOS déclarés, sur 50 générations | 37 | 40 | 41 |

Le SFT réduit la perte sur ce corpus réservé. Le DPO change peu cette mesure et 43 sorties sur 50 sont identiques au SFT. Ce constat n'est pas un test de significativité ni une mesure de justesse clinique. Les drapeaux EOS sont recomptés depuis les sorties sauvegardées, pas recalculés avec le tokenizer. Voir la [preuve finale v35](../docs/evidence/FINAL_QA_V35_RESULT.md).

## 5. DPO : préparation et limites

Le lot UltraMedical initial contenait 512 paires train et 64 validations, toutes anglaises. Après revue contextuelle, 95 récits personnels non vérifiés et une paire altérée ont été exclus. Le candidat filtré contient 426 train et 54 validation ; son usage expérimental est consigné dans ADR-014, sans approbation clinique ni revue humaine indépendante. Les statistiques suivantes décrivent le lot initial. Les catégories source comprennent `length`, `easy` et `hard`. La réponse préférée est plus longue en caractères dans 358/512 paires train ; ce constat descriptif ne prouve pas un biais causal. Certaines paires choisissent la même option finale avec des explications différentes. `chosen/rejected` ne signifie donc pas automatiquement « triage correct/incorrect », et le DPO ne peut pas être présenté comme une garantie de prudence.

Le raccord DPO ne dépend plus de l'ancien hash v5 : il vérifie un manifeste explicite du SFT, de son tokenizer et de la comparaison associée. Le contrôle local des longueurs n'a trouvé aucun dépassement des budgets de 1 024 tokens de prompt et 2 048 tokens par séquence complète sur les 576 paires. La revue technique et contextuelle a conduit aux exclusions ci-dessus ; aucune approbation clinique n'a été créée.

La v27 a exécuté vingt étapes sur T4 en 464,143 secondes, beta 0,1, learning rate `5e-6`, batch effectif 8. Les 392 tenseurs de la politique ont changé ; la référence est restée identique au SFT initial. Les poids sauvegardés ont été téléchargés et vérifiés contre les empreintes du run. Sur 54 paires de validation, la loss DPO passe de 0,63323 à l'étape 10 à 0,62233 à l'étape 20. Le taux de préférence implicite TRL est 64,8 % ; ce n'est pas une accuracy médicale. La comparaison v28 terminée donne une NLL de 0,786970 pour SFT contre 0,786059 pour DPO, mais seulement 1/18 JSON de triage conforme pour chacun. Le runtime diffère de v26 ; aucun gain de triage n’est démontré. Voir [résultats v28](../docs/evidence/COMPARAISON_V28_RESULT_2026-09-13.md).

Le faible effet observé peut être lié à un essai court et à des préférences de réponses médicales générales, toutes anglaises, qui ne ciblent pas directement les priorités de triage. Ce sont des hypothèses, pas des causes isolées expérimentalement. Les poids vérifiés confirment une optimisation effective ; augmenter simplement le nombre d'étapes ne garantit pas une amélioration.

Preuves : [résultat v27](../docs/evidence/DPO_V27_RESULT_2026-09-13.md), [lancement v28](../docs/evidence/COMPARAISON_V28_LAUNCH_2026-09-13.md), [raccord DPO](../docs/evidence/DPO_HANDOFF_2026-09-12.md), [revue descriptive](../docs/evidence/DPO_CANDIDATE_REVIEW_2026-09-12.json).

## 6. API, audit et déploiement

`POST /v1/triage` valide le contrat, retourne un niveau parmi les trois autorisés, ajoute un avertissement FR/EN et un identifiant d'interaction. Le fournisseur compatible vLLM anonymise les entrées avant transport et demande une sortie conforme au schéma. La factory privée exige un jeton. L'application par défaut n'a aucun modèle configuré et retourne 503 au triage.

L’exécution v34 a servi les adaptateurs sauvegardés via vLLM 0.15.0, en FP16 avec sortie JSON contrainte, sur 18 scénarios synthétiques par variante. Après identification de générations incomplètes en v33, un prompt et un schéma plus concis ainsi qu’un budget de 768 tokens permettent 18 réponses API conformes sur 18 pour SFT et DPO. Ces changements ont été appliqués ensemble : leur contribution individuelle n’est pas isolée.

Les deux variantes donnent les mêmes priorités : 8/18 correspondent aux références proposées, dont les six cas critiques classés `maximum`. Aucune réponse ne propose `moderate`, et les cas d’informations insuffisantes ne reçoivent pas de question complémentaire. Une réponse anglaise suppose aussi une stabilité absente des informations fournies. Le parcours reste donc incomplet ; aucune amélioration du triage par DPO n’est démontrée.

Les latences médianes client sont de 7,719 secondes pour SFT et 7,178 secondes pour DPO ; p95 : 38,323 et 22,011 secondes. Les mesures sont séquentielles et ne constituent pas un test de charge. Le DPO passe après le SFT dans le même serveur ; l’effet des caches interdit d’attribuer directement la différence au DPO. Les 18 réponses de chaque variante correspondent chacune à une trace d’audit. Voir la [preuve v34](../docs/evidence/VLLM_API_V34_RESULT.md). Ces mesures ne prouvent ni la justesse clinique ni l’accès extérieur au service.

Une extension locale de collecte (API 0.3.0) suit les rubriques renseignées, les absences explicitement déclarées et les informations indisponibles. Les questions FR/EN avancent au fil des contextes consolidés. Le raccord est testé avec fournisseur simulé ; il n'est pas inclus dans les mesures GPU v34 et ne prouve pas une amélioration de la priorité. Voir le [parcours de collecte](../docs/technical/COLLECTE_COMPLEMENTAIRE_V1.md).

L'audit local conserve désormais le contexte anonymisé transmis au modèle et la réponse délivrée, avec identifiant, versions, statut et durée. Les textes de sortie sont aussi contrôlés avant restitution. Un test d'intégration avec modèle et anonymiseur simulés vérifie la correspondance HTTP/JSONL et les refus en cas d'échec. Cette [preuve locale](../docs/evidence/API_AUDIT_CONTENT_2026-09-12.md) ne valide ni la détection exhaustive des identifiants ni la persistance distante. Deux processus API locaux successifs ont également conservé les réponses dans le même journal. La synchronisation du fichier est exigée avant restitution ; son échec produit un refus 503. Cette [preuve locale de redémarrage](../docs/evidence/AUDIT_RESTART_LOCAL_2026-09-14.md) ne prouve pas la durabilité du futur volume distant. La politique de stockage et de conservation reste à définir avant déploiement.

La régression locale complète passe 215 tests au 16 septembre. La v37 a exécuté Base/SFT/DPO via la même API et deux dialogues de six échanges FR/EN. Les garde-fous empêchent les mesures critiques manquantes et les retards dangereux observés, mais interviennent sur 13/18 sorties SFT et 14/18 sorties DPO ; ils ne transforment pas ces mesures en validation clinique. L'image API se construit localement et les modes sans fournisseur et factory privée authentifiée passent hors réseau. La configuration GitHub Actions couvre tests et conteneur ; le déploiement automatisé et son exécution distante restent à terminer. L'unique autorisation GPU actuelle est le notebook Kaggle privé sur quota gratuit. Un endpoint cloud nécessite une cible et un coût explicitement autorisés, puis une démonstration du modèle via vLLM et FastAPI. Aucun endpoint ni modèle public n'est annoncé.

Preuves : [validation locale historique](../docs/evidence/POST_SFT_IMPLEMENTATION_2026-09-05.md), [évaluation de l'endpoint](../docs/technical/EVALUATION_ENDPOINT_V1.md).

## 7. Conditions de clôture et limites

La recharge de l'ancien SFT est établie par v25 ; celle du nouveau SFT v39 reste soumise à v40. Les comparaisons historiques QA du DPO, sur validation et test, sont réalisées et conservées comme baseline négative. Une nouvelle réserve synthétique FR/EN de 18 cas a été gelée avant le résultat v39 ; elle ne sera ouverte qu'une fois le nouveau SFT et son DPO sélectionnés. La clôture nécessite encore le nouveau DPO borné, l'ouverture unique de cette réserve, une démonstration sur cible accessible autorisée, le déploiement GitHub Actions et le PDF final avec ses preuves.

Les résultats automatiques, la revue humaine et la validation clinique sont distincts. Aucun rappel critique, taux de sous-triage ou de réponses dangereuses n'est établi sur une référence cliniquement validée. Les sources de connaissances et préférences ouvertes ne remplacent pas cette référence. Le niveau de validation attendu pour la soutenance doit être clarifié avec le mentor, sans attribuer une validation fictive au travail réalisé.

L'évaluation doit documenter les résultats négatifs aussi bien que les gains. Le POC peut produire une comparaison expérimentale utile même si le DPO n'améliore pas tous les indicateurs ; cela ne dispense pas de réaliser les livrables ni de signaler les limites. L'usage clinique autonome demeure hors périmètre.
