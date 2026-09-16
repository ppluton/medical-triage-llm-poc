# Rapport technique — POC d'assistance au triage médical CHSA

- **Date :** 2026-09-16
- **Statut :** draft finalisé côté modèle — démonstration extérieure sans dépense préparée
- **Sources :** [cadrage](../CADRAGE_MISSION.md), [spécification](../SPEC_POC_TRIAGE_MEDICAL.md), [audit de mission](../docs/evidence/AUDIT_ALIGNEMENT_MISSION_2026-09-12.md) et preuves liées ci-dessous.
- **Format final :** candidat PDF de cinq pages généré et vérifié ; le nom de remise définitif dépend encore de l'identité et du mois de démarrage confirmés.

## 1. Objectif et état du POC

Le CHSA souhaite un assistant de triage initial qui recueille les symptômes, demande les informations utiles, propose l'un des niveaux `maximum`, `moderate` ou `deferred`, explique sa proposition et conserve une trace exploitable. Ce projet d'étude doit démontrer une faisabilité technique ; il ne constitue pas un outil de diagnostic, de prescription ou de décision clinique autonome.

La chaîne actuelle comprend un corpus bilingue v2.2 finalisé par des contrôles techniques de confidentialité, un SFT LoRA de Qwen3-1.7B-Base à 150 étapes et un DPO borné réancré sur ce SFT. La v40 recharge le SFT avec 30/30 générations identiques. La comparaison v43 montre que DPO améliore plusieurs métriques de forme QA, mais ajoute un flag diagnostic/prescriptif dans la revue aveugle ; le SFT v39 est donc retenu avant ouverture de la réserve. Sur les 18 cas synthétiques finaux v46, le SFT produit 0 JSON conforme, atteint le plafond sur 17 sorties et répète fortement. L’intégration vLLM/API avec schéma contraint et garde-fous reste une démonstration technique utile, mais aucun gain de pertinence clinique ni déploiement hospitalier n'est établi.

| Livrable demandé | Preuve disponible | Écart restant |
|---|---|---|
| Dataset bilingue documenté | SFT v2.2 : 4 700 lignes, 31 masques sur 22 lignes, zéro identifiant direct au rescan | Publication externe, certification RGPD et validation clinique absentes |
| SFT puis DPO comparés | SFT v39 rechargé ; DPO v41 vérifié ; sélection v43 et réserve v46 terminées | Validation clinique indépendante absente ; triage brut final non conforme |
| Endpoint cloud vLLM/API | Intégration réelle v37 ; parcours Kaggle + Cloudflare à 0 € implémenté | Lancer le notebook et conserver URL, smoke et audit extérieurs |
| GitHub Actions tests/déploiement | Tests et conteneur passés sur la PR #4 ; 245 tests locaux sur le parcours gratuit | Quick Tunnel interactif, pas de CD GPU permanente prouvée |
| Rapport et soutenance | Rapport et support générés à partir des preuves finales du modèle | Nommage final et démonstration extérieure |

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

Afin que les poids livrés correspondent au corpus final, la v39 redémarre depuis la Base exacte et entraîne 150 étapes sur v2.2. Son adaptateur porte le SHA-256 `c911f9c631be825f4af5c7dff5a87409d1ee91d4c28e2b0b1571e808e055d413`. Les 392 tenseurs LoRA sont finis et modifiés ; la NLL validation atteint 0,711802. Huit générations sur trente atteignent encore le plafond, toutes sur MedQuAD. La v40 recharge ensuite ce checkpoint dans un nouveau processus : 30/30 générations sont identiques et le delta absolu de loss vaut zéro.

Preuves : [SFT historique](../docs/evidence/SFT_KAGGLE_FULL_RUN_2026-09-04.md), [pilote final v39](../docs/evidence/SFT_V39_RESULT_2026-09-16.md) et [recharge v40](../docs/evidence/SFT_V40_RELOAD_RESULT_2026-09-16.md).

## 4. Comparaison finale de développement et choix du modèle

La v43 recharge Base, SFT v39 et DPO v41 dans le même runtime 4 bits. Elle utilise les mêmes
479 validations pour la NLL, trente prompts QA pour la génération et dix-huit scénarios
synthétiques de développement. Aucun test ou cas de réserve n’est utilisé. Les métriques QA
sont recalculées depuis les observations sauvegardées :

| Mesure de développement | Base | SFT v39 | DPO v41 |
|---|---:|---:|---:|
| NLL moyenne, 479 validations | 1,532045 | 0,830098 | 0,828884 |
| EOS, sur 30 | 23 | 24 | 26 |
| Plafond 512 tokens, sur 30 | 7 | 6 | 4 |
| Réponses exactes normalisées, sur 30 | 0 | 5 | 5 |
| Fraction de 4-grammes répétés | 0,2682 | 0,1860 | 0,1420 |

DPO améliore la terminaison et la répétition, mais pas le nombre de réponses exactes. Sur le
triage brut, Base produit 0 JSON valide et SFT/DPO seulement 1/18 chacun. La revue aveugle des
54 sorties signale les 54 ; DPO ajoute une formulation diagnostique/prescriptive par rapport au
SFT. La règle fixée avant lecture exigeait une domination sans régression : SFT v39 est donc
retenu. Ce choix conservateur ne constitue pas une validation clinique.

## 5. DPO et réserve finale

Le lot DPO v3 contient 426 paires train et 54 validation issues d’UltraMedical-Preference,
toutes anglaises. Les 480 charges sont inchangées par rapport à la source filtrée et ne
recouvrent aucun prompt SFT v2.2. Les préférences n’annotent pas directement les priorités de
triage et ne sont pas validées cliniquement.

La v41 exécute vingt étapes depuis le SFT v39. Les 392 tenseurs de politique changent, la
référence reste identique et l’adaptateur final est vérifié. La loss DPO validation passe de
0,6355 à l’étape 10 à 0,6268 à l’étape 20 ; la préférence implicite atteint 66,7 %. Ces mesures
prouvent une optimisation, pas une meilleure décision médicale. La sélection v43 ne retient
pas cet adaptateur supplémentaire.

Après la décision, la v46 évalue une seule fois le SFT sur les 18 scénarios FR/EN gelés. Le
snapshot Base est contrôlé par checksum, DPO n’est pas chargé et aucune optimisation n’a lieu :

| Mesure de réserve | SFT sélectionné |
|---|---:|
| JSON conformes | 0 / 18 |
| Arrêts EOS | 1 / 18 |
| Plafond 512 tokens | 17 / 18 |
| Fraction de 4-grammes répétés | 0,8289 |
| Latence séquentielle p50 / p95 | 52,707 s / 53,591 s |

Les dix-huit sorties sont signalées comme malformées ou répétitives. La revue bornée détecte
au moins six faits patient non étayés, deux formulations diagnostiques/prescriptives et cinq
priorités inférieures à `maximum` sur des cas proposés critiques. Ce résultat négatif est
final : il ne sert pas à retoucher les poids, le prompt ou les garde-fous.

Preuves : [DPO v41](../docs/evidence/DPO_V41_RESULT_2026-09-16.md), [comparaison et sélection v43](../docs/evidence/COMPARISON_V43_RESULT_2026-09-16.md), [réserve v46](../docs/evidence/SELECTED_RESERVE_V46_RESULT_2026-09-16.md).

## 6. API, audit et déploiement

`POST /v1/triage` valide le contrat, retourne un niveau parmi les trois autorisés, ajoute un avertissement FR/EN et un identifiant d'interaction. Le fournisseur compatible vLLM anonymise les entrées avant transport et demande une sortie conforme au schéma. La factory privée exige un jeton. L'application par défaut n'a aucun modèle configuré et retourne 503 au triage.

L’exécution v34 a servi les adaptateurs sauvegardés via vLLM 0.15.0, en FP16 avec sortie JSON contrainte, sur 18 scénarios synthétiques par variante. Après identification de générations incomplètes en v33, un prompt et un schéma plus concis ainsi qu’un budget de 768 tokens permettent 18 réponses API conformes sur 18 pour SFT et DPO. Ces changements ont été appliqués ensemble : leur contribution individuelle n’est pas isolée. La réserve v46 démontre rétrospectivement que cette conformité provient de la couche de service contrainte, et non d’une capacité fiable du modèle brut.

Les deux variantes donnent les mêmes priorités : 8/18 correspondent aux références proposées, dont les six cas critiques classés `maximum`. Aucune réponse ne propose `moderate`, et les cas d’informations insuffisantes ne reçoivent pas de question complémentaire. Une réponse anglaise suppose aussi une stabilité absente des informations fournies. Le parcours reste donc incomplet ; aucune amélioration du triage par DPO n’est démontrée.

Les latences médianes client sont de 7,719 secondes pour SFT et 7,178 secondes pour DPO ; p95 : 38,323 et 22,011 secondes. Les mesures sont séquentielles et ne constituent pas un test de charge. Le DPO passe après le SFT dans le même serveur ; l’effet des caches interdit d’attribuer directement la différence au DPO. Les 18 réponses de chaque variante correspondent chacune à une trace d’audit. Voir la [preuve v34](../docs/evidence/VLLM_API_V34_RESULT.md). Ces mesures ne prouvent ni la justesse clinique ni l’accès extérieur au service.

Une extension locale de collecte (API 0.3.0) suit les rubriques renseignées, les absences explicitement déclarées et les informations indisponibles. Les questions FR/EN avancent au fil des contextes consolidés. Le raccord est testé avec fournisseur simulé ; il n'est pas inclus dans les mesures GPU v34 et ne prouve pas une amélioration de la priorité. Voir le [parcours de collecte](../docs/technical/COLLECTE_COMPLEMENTAIRE_V1.md).

L'audit local conserve désormais le contexte anonymisé transmis au modèle et la réponse délivrée, avec identifiant, versions, statut et durée. Les textes de sortie sont aussi contrôlés avant restitution. Un test d'intégration avec modèle et anonymiseur simulés vérifie la correspondance HTTP/JSONL et les refus en cas d'échec. Cette [preuve locale](../docs/evidence/API_AUDIT_CONTENT_2026-09-12.md) ne valide ni la détection exhaustive des identifiants ni la persistance distante. Deux processus API locaux successifs ont également conservé les réponses dans le même journal. La synchronisation du fichier est exigée avant restitution ; son échec produit un refus 503. Cette [preuve locale de redémarrage](../docs/evidence/AUDIT_RESTART_LOCAL_2026-09-14.md) ne prouve pas la durabilité du futur volume distant. La politique de stockage et de conservation reste à définir avant déploiement.

La régression locale complète passe 245 tests au 16 septembre. La v37 a exécuté Base/SFT/DPO via la même API et deux dialogues de six échanges FR/EN. Les garde-fous empêchent les mesures critiques manquantes et les retards dangereux observés, mais interviennent sur 13/18 sorties SFT et 14/18 sorties DPO ; ils ne transforment pas ces mesures en validation clinique. L'image API se construit localement et les modes sans fournisseur et factory privée authentifiée passent hors réseau.

Pierre a fixé une contrainte de dépense nulle. L'ADR-019 remplace donc la proposition Modal par une démonstration interactive : Kaggle fournit la T4 gratuite déjà utilisée par le projet et Cloudflare Quick Tunnel une URL HTTPS temporaire. Le notebook privé attache uniquement le snapshot Base et le SFT v39, vérifie leurs checksums et celui de `cloudflared`, conserve vLLM/FastAPI en boucle locale et expose seulement l'API authentifiée. Le contrat local et la régression passent 245 tests. Aucun GPU, endpoint ou service payant n'a été créé. L'URL réelle, le smoke extérieur et l'audit de session restent à observer ; Quick Tunnel est sans SLA et n'est pas une CD GPU permanente.

Preuves : [validation locale historique](../docs/evidence/POST_SFT_IMPLEMENTATION_2026-09-05.md), [évaluation de l'endpoint](../docs/technical/EVALUATION_ENDPOINT_V1.md), [préparation sans dépense](../docs/evidence/FREE_DEMO_PREPARATION_2026-09-16.md) et [CI GitHub](../docs/evidence/GITHUB_CI_MODAL_PREPARATION_2026-09-16.md).

## 7. Conditions de clôture et limites

La recharge du SFT v39, le DPO v41, la comparaison v43 et l'ouverture unique de la réserve v46 sont terminés. Le résultat final interdit toute conclusion favorable sur le triage brut : le composant modèle nécessite le schéma contraint, les garde-fous et la décision humaine. Le candidat PDF et le support de soutenance ont été générés et contrôlés localement ; leur nom de remise doit encore être confirmé. La clôture de démonstration nécessite encore une session Kaggle active, l'URL Cloudflare éphémère et un smoke test distant ; elle ne nécessite plus de budget.

Les résultats automatiques, la revue humaine et la validation clinique sont distincts. Aucun rappel critique, taux de sous-triage ou de réponses dangereuses n'est établi sur une référence cliniquement validée. Les sources de connaissances et préférences ouvertes ne remplacent pas cette référence. Le niveau de validation attendu pour la soutenance doit être clarifié avec le mentor, sans attribuer une validation fictive au travail réalisé.

L'évaluation doit documenter les résultats négatifs aussi bien que les gains. Le POC peut produire une comparaison expérimentale utile même si le DPO n'améliore pas tous les indicateurs ; cela ne dispense pas de réaliser les livrables ni de signaler les limites. L'usage clinique autonome demeure hors périmètre.
