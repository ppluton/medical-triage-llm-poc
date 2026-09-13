# Rapport technique — POC d'assistance au triage médical CHSA

- **Date :** 2026-09-12
- **Statut :** draft — rapport intermédiaire, livrables incomplets
- **Sources :** [cadrage](../CADRAGE_MISSION.md), [spécification](../SPEC_POC_TRIAGE_MEDICAL.md), [audit de mission](../docs/evidence/AUDIT_ALIGNEMENT_MISSION_2026-09-12.md) et preuves liées ci-dessous.
- **Format final :** PDF de vingt pages maximum ; ce document Markdown n'est pas encore le PDF final.

## 1. Objectif et état du POC

Le CHSA souhaite un assistant de triage initial qui recueille les symptômes, demande les informations utiles, propose l'un des niveaux `maximum`, `moderate` ou `deferred`, explique sa proposition et conserve une trace exploitable. Ce projet d'étude doit démontrer une faisabilité technique ; il ne constitue pas un outil de diagnostic, de prescription ou de décision clinique autonome.

La chaîne actuelle comprend un corpus bilingue corrigé, un SFT général de Qwen3-1.7B-Base à 500 étapes et une comparaison QA avec la Base. L'API dispose de contrats et de tests locaux, mais son intégration au vrai modèle via vLLM n'est pas démontrée. Un essai DPO de vingt étapes est terminé (v27), avec poids sauvegardés vérifiés. La comparaison commune v28 est terminée : Base 0/18 JSON conformes, SFT et DPO 1/18 chacun dans le runtime Transformers FP4. Aucun gain de triage DPO n’est démontré. Aucun gain de pertinence clinique ni déploiement hospitalier n'est établi.

| Livrable demandé | Preuve disponible | Écart restant |
|---|---|---|
| Dataset bilingue documenté | SFT v2.1 : 4 700 lignes, provenance et transformations suivies | Lot DPO 426/54 admis pour expérimentation pédagogique ; validation clinique absente |
| SFT puis DPO comparés | Comparaison commune v28 terminée, sans gain de triage DPO | Écart de runtime à expliquer ; test réservé à effectuer |
| Endpoint cloud vLLM/API | Contrats FastAPI, transport simulé, packaging local | Vrai modèle, cible cloud autorisée, démonstration et latence |
| GitHub Actions tests/déploiement | Workflow de tests et conteneur écrit | Exécution distante vérifiée et déploiement automatisé |
| Rapport et soutenance | Présente synthèse et preuves intermédiaires | Mesures finales, PDF ≤20 pages et démonstration |

## 2. Données et gouvernance

Les sources retenues sont MediQAl, FrenchMedMCQA et MedQuAD pour le SFT, et UltraMedical-Preference pour le DPO. La provenance, les licences et les transformations sont décrites dans les manifestes et documents de gouvernance. Les liens de l'école vers FrenchMedMCQA et MedQuAD sont mal formés ; les familles de sources correspondent, mais l'équivalence exacte des reconditionnements n'est pas établie par l'audit. Les données brutes et les poids restent hors Git.

Le premier corpus comptait 5 000 lignes. Notre transformation perdait des propositions QCM dans 2 249 des 2 250 QCM de développement, tronquait 101 réponses et n'enseignait pas correctement l'arrêt natif de la réponse. Ces erreurs relèvent de notre préparation, pas d'une défaillance démontrée des sources. Les corrections et exclusions documentées conduisent au corpus v2.1 :

| Split | Lignes | Usage |
|---|---:|---|
| Train | 3 721 | Optimisation SFT |
| Validation | 479 | Suivi, comparaison et choix de développement |
| Test | 500 | Évaluation finale réservée ; non utilisée pour régler le modèle |

Les choix et réponses complets, le masquage du prompt et la présence d'un EOS supervisé ont été contrôlés sur les 4 200 exemples de développement. Le corpus reste bilingue, sans imposer l'égalité du nombre de tokens français et anglais. Les réponses MedQuAD sont souvent longues ; l'équilibre des lignes ne garantit donc pas l'équilibre des tokens. La cible scolaire est d'environ 5 000 paires, avec priorité à la qualité.

Les réponses QA sources ne sont pas des annotations de priorité de triage. Les scans d'identifiants et la revue technique ne sont pas une validation clinique ni une preuve d'anonymisation exhaustive. Les scénarios de démonstration sont synthétiques et leurs références portent le statut `proposed_educational_only`.

Preuves : [audit de pipeline](../docs/evidence/PIPELINE_AUDIT_2026-09-05.md), [audit de réalignement](../docs/evidence/AUDIT_ALIGNEMENT_MISSION_2026-09-12.md), [manifeste SFT corrigé](../data/manifests/derived-source-medical-qa-sft-v2.1-reviewed.json).

## 3. Méthode et entraînements SFT

La base est `unsloth/Qwen3-1.7B-Base`, révision `e249956c10337100486d07afb77e3eb2b30906b8`. La recette corrigée utilise le chargement 4 bits, LoRA de rang et alpha 16, batch effectif 8, contexte de 2 048 tokens, learning rate initial `1e-4` et seed 42. La loss supervise uniquement la réponse et son EOS. Le calcul utilise FP16 AMP, avec paramètres entraînables LoRA maintenus en FP32. Les versions CUDA et bibliothèques sont consignées dans la configuration du run.

L'entraînement historique v5 du 4 septembre a exécuté 1 000 étapes sur le premier corpus. Son exécution technique a abouti, mais ses répétitions et les défauts de préparation empêchent d'en faire la référence courante. Les résultats historiques restent archivés ; ils ne sont pas directement comparables aux pertes recalculées avec un corpus et une agrégation différents.

Le SFT corrigé a progressé jusqu'à 150 puis 500 étapes. La continuation v22 a restauré optimiseur, scheduler, scaler et RNG ; elle a ajouté 350 étapes en environ 26 min 41 s, évaluations périodiques incluses. Le checkpoint atteint environ 1,073 époque. Ses fichiers ont été archivés et leurs empreintes contrôlées. Le diagnostic distinct de mémorisation sur douze exemples ne sert pas de modèle général ni de point de départ au DPO.

L'adaptateur SFT 500 a pour SHA-256 `5c195a8c83bfd6493e7ffd74ec20e3d97207f9b650850aabd8de25afffea626d`. Une archive correcte ne prouve pas à elle seule que l'inférence dans un nouveau processus reproduit les sorties.

Preuves : [SFT historique](../docs/evidence/SFT_KAGGLE_FULL_RUN_2026-09-04.md), [résultat v22](../docs/evidence/SFT_V22_RESULT_2026-09-12.md), [identité du checkpoint](../configs/sft-v22-handoff.json).

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

## 5. DPO : préparation et limites

Le lot UltraMedical initial contenait 512 paires train et 64 validations, toutes anglaises. Après revue contextuelle, 95 récits personnels non vérifiés et une paire altérée ont été exclus. Le candidat filtré contient 426 train et 54 validation ; son usage expérimental est consigné dans ADR-014, sans approbation clinique ni revue humaine indépendante. Les statistiques suivantes décrivent le lot initial. Les catégories source comprennent `length`, `easy` et `hard`. La réponse préférée est plus longue en caractères dans 358/512 paires train ; ce constat descriptif ne prouve pas un biais causal. Certaines paires choisissent la même option finale avec des explications différentes. `chosen/rejected` ne signifie donc pas automatiquement « triage correct/incorrect », et le DPO ne peut pas être présenté comme une garantie de prudence.

Le raccord DPO ne dépend plus de l'ancien hash v5 : il vérifie un manifeste explicite du SFT, de son tokenizer et de la comparaison associée. Le contrôle local des longueurs n'a trouvé aucun dépassement des budgets de 1 024 tokens de prompt et 2 048 tokens par séquence complète sur les 576 paires. La revue technique et contextuelle a conduit aux exclusions ci-dessus ; aucune approbation clinique n'a été créée.

La v27 a exécuté vingt étapes sur T4 en 464,143 secondes, beta 0,1, learning rate `5e-6`, batch effectif 8. Les 392 tenseurs de la politique ont changé ; la référence est restée identique au SFT initial. Les poids sauvegardés ont été téléchargés et vérifiés contre les empreintes du run. Sur 54 paires de validation, la loss DPO passe de 0,63323 à l'étape 10 à 0,62233 à l'étape 20. Le taux de préférence implicite TRL est 64,8 % ; ce n'est pas une accuracy médicale. La comparaison v28 terminée donne une NLL de 0,786970 pour SFT contre 0,786059 pour DPO, mais seulement 1/18 JSON de triage conforme pour chacun. Le runtime diffère de v26 ; aucun gain de triage n’est démontré. Voir [résultats v28](../docs/evidence/COMPARAISON_V28_RESULT_2026-09-13.md).

Preuves : [résultat v27](../docs/evidence/DPO_V27_RESULT_2026-09-13.md), [lancement v28](../docs/evidence/COMPARAISON_V28_LAUNCH_2026-09-13.md), [raccord DPO](../docs/evidence/DPO_HANDOFF_2026-09-12.md), [revue descriptive](../docs/evidence/DPO_CANDIDATE_REVIEW_2026-09-12.json).

## 6. API, audit et déploiement

`POST /v1/triage` valide le contrat, retourne un niveau parmi les trois autorisés, ajoute un avertissement FR/EN et un identifiant d'interaction. Le fournisseur compatible vLLM anonymise les entrées avant transport et demande une sortie conforme au schéma. La factory privée exige un jeton. L'application par défaut n'a aucun modèle configuré et retourne 503 au triage.

Les tests locaux avec transport simulé prouvent les contrats et les chemins d'erreur couverts. Ils ne prouvent pas une génération du vrai modèle. Le conteneur a été vérifié localement sans serveur de modèle. Le programme d'évaluation de l'endpoint mesure les réponses valides, les identifiants uniques et les latences p50/p95 ; son existence ne constitue pas une mesure distante.

L'audit local conserve désormais le contexte anonymisé transmis au modèle et la réponse délivrée, avec identifiant, versions, statut et durée. Les textes de sortie sont aussi contrôlés avant restitution. Un test d'intégration avec modèle et anonymiseur simulés vérifie la correspondance HTTP/JSONL et les refus en cas d'échec. Cette [preuve locale](../docs/evidence/API_AUDIT_CONTENT_2026-09-12.md) ne valide ni la détection exhaustive des identifiants ni la persistance distante. La politique de stockage et de conservation reste à définir avant déploiement.

La configuration GitHub Actions couvre tests et conteneur ; le déploiement automatisé et son exécution distante restent à terminer. L'unique autorisation GPU actuelle est le notebook Kaggle privé sur quota gratuit. Un endpoint cloud nécessite une cible et un coût explicitement autorisés, puis une démonstration du modèle via vLLM et FastAPI. Aucun endpoint ni modèle public n'est annoncé.

Preuves : [validation locale historique](../docs/evidence/POST_SFT_IMPLEMENTATION_2026-09-05.md), [évaluation de l'endpoint](../docs/technical/EVALUATION_ENDPOINT_V1.md).

## 7. Conditions de clôture et limites

La recharge du SFT est établie par v25. La clôture nécessite une comparaison du DPO exécuté selon le même protocole, une évaluation finale réservée après gel des choix et une démonstration de bout en bout. Elle comprend aussi l'audit conforme au mandat, les mesures de latence, le déploiement GitHub Actions et le PDF final avec ses preuves.

Les résultats automatiques, la revue humaine et la validation clinique sont distincts. Aucun rappel critique, taux de sous-triage ou de réponses dangereuses n'est établi sur une référence cliniquement validée. Les sources de connaissances et préférences ouvertes ne remplacent pas cette référence. Le niveau de validation attendu pour la soutenance doit être clarifié avec le mentor, sans attribuer une validation fictive au travail réalisé.

L'évaluation doit documenter les résultats négatifs aussi bien que les gains. Le POC peut produire une comparaison expérimentale utile même si le DPO n'améliore pas tous les indicateurs ; cela ne dispense pas de réaliser les livrables ni de signaler les limites. L'usage clinique autonome demeure hors périmètre.
