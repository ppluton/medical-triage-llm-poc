# Rapport technique — POC d'assistance au triage médical CHSA

- **Date :** 2026-09-05
- **Statut :** draft — rapport intermédiaire fondé sur les preuves disponibles
- **Sources :** cadrage, spécification, manifestes versionnés, preuves SFT du 4 septembre et validation post-SFT du 5 septembre.
- **Limite éditoriale :** maximum 20 pages lors de la clôture.

## 1. Résumé exécutif

Le projet démontre à ce stade une chaîne de données traçable et un entraînement SFT complet de Qwen3-1.7B-Base sur Kaggle privé. Il dispose d'une API testée localement et d'un conteneur fonctionnel sans serveur de modèle configuré. La comparaison Base/SFT montre une loss réponse réduite de 2,10444 à 1,52624 sur 500 validations. Toutefois, les 30 générations SFT atteignent le plafond de tokens et plusieurs sont répétitives. Aucun gain clinique n’est déclaré ; le passage DPO est suspendu au diagnostic de génération.

La clôture du POC nécessite encore un DPO exécuté et comparé, une évaluation de sûreté revue, une inférence réelle via l'API et les mesures de latence. Le projet n'est ni un dispositif médical, ni un outil de diagnostic ou de prescription, ni une décision clinique autonome.

## 2. Données et gouvernance

Les sources ouvertes, licences, révisions et transformations sont décrites dans les manifestes et data cards du dépôt. Le corpus SFT source contient 5 000 exemples, répartis en 4 000 entraînements, 500 validations et 500 tests. Le test final reste isolé. Les données et poids lourds restent hors Git.

Les réponses sources de QA ne sont pas des annotations de priorités de triage. De même, les préférences biomédicales ne prouvent pas une préférence cliniquement valide pour le contrat du POC. Les scans automatiques d'identifiants n'établissent pas à eux seuls l'anonymisation exhaustive.

## 3. Méthode et SFT observé

Base : `unsloth/Qwen3-1.7B-Base`, révision `e249956c10337100486d07afb77e3eb2b30906b8`. Le SFT v5 a terminé 1 000 étapes, deux epochs, batch effectif 8 et contexte maximal 2 048 tokens. LoRA : rang/alpha 16 ; LR initial `1e-4` ; seed 42 ; chargement 4 bits et calcul FP16.

Le run sur Tesla T4 a duré environ 3 h 41 min au total. L'adaptateur retenu correspond au checkpoint 1 000 ; son SHA-256 est `3f050ae77a4b66ecf4a254a407a463a046143437198ac5dfbd7922b75b28a940`. L'archive a été téléchargée et contrôlée. La loss d'évaluation du trainer vaut environ 1,2815 ; elle ne mesure ni un taux de réponses exactes ni la sûreté du triage.

Preuve : [SFT complet](../docs/evidence/SFT_KAGGLE_FULL_RUN_2026-09-04.md).

## 4. Comparaison et DPO

La comparaison QA applique aux modèles le même tokenizer archivé, les mêmes 500 conversations de validation et les mêmes paramètres. Elle mesure la vraisemblance des références, avec agrégation pondérée par token, et conserve 30 générations par modèle pour revue. Une sonde additionnelle couvre huit catégories synthétiques et le respect du schéma JSON ; elle est préparée mais non exécutée dans le run v8.

Le runner DPO utilise une politique initialisée depuis le SFT et une copie de référence figée. Il refuse l'absence de comparaison terminée, de décision tracée et de données approuvées pour l'expérimentation. La recette initiale prévoit 20 étapes, beta 0,1, LR `5e-6`, batch effectif 8. Ce code n'est pas une preuve d'entraînement DPO terminé.

512 paires train et 64 validations sont préparées en anglais. Le premier lot a été rejeté pour masquages NER erronés ; le second reste candidat avec revue de confidentialité et de contenu à réaliser. Aucun test final n'a servi à ajuster le modèle.

La comparaison Kaggle v8 a été téléchargée et ses agrégats recalculés à l'identique. Six sorties SFT sur 30 contiennent des caractères CJK ; Base en compte zéro. L'agrégat de loss pondéré est dominé par les tokens EN. La baisse de loss n'établit pas une meilleure qualité de génération. Les diagnostics v10/v11 n'ont pas corrigé les répétitions par un arrêt de message explicite, NF4 ou FP16 sans quantification, sur trois exemples. Le contrôle v13 avec Unsloth reproduit également le défaut. Une correction du SFT doit être testée avant le DPO. Voir [la preuve comparative et ses limites](../docs/evidence/BASE_SFT_KAGGLE_2026-09-05.md).

## 5. API, audit et packaging

`POST /v1/triage` valide et normalise les champs, limite les sorties à `maximum`, `moderate`, `deferred`, ajoute l'avertissement FR/EN et un identifiant d'interaction. Le fournisseur compatible vLLM anonymise le contexte avant transport et refuse un résultat invalide ou tronqué. La factory privée exige un jeton ; l'application par défaut n'a aucun modèle et retourne 503 pour le triage.

L'audit enregistre identifiant, versions, statut et durée, sans texte médical. Cette minimisation ne satisfait pas encore l'exigence du brief de conserver des entrées anonymisées et des sorties auditables : le contenu et la conservation doivent être décidés.

Les tests prouvent les contrats locaux avec transport simulé. L'image Docker corrigée a été construite et testée sans réseau avec les vrais modèles d'anonymisation. Le job CI de conteneur est écrit mais n'a pas été observé sur GitHub. Aucune preuve d'inférence vLLM réelle ni de pilote hospitalier n'est disponible.

Preuve : [validation post-SFT](../docs/evidence/POST_SFT_IMPLEMENTATION_2026-09-05.md).

## 6. Limites et résultats négatifs

- Validation de développement distincte d'un test final indépendant.
- Loss QA distincte de justesse médicale et de qualité de triage.
- Préférences candidates uniquement anglaises, non revues cliniquement.
- Faux positifs de masquage observés et lot initial rejeté.
- Garde-fous cliniques proposés, non validés ; une instruction de prompt ne prouve pas leur respect.
- Rappel critique, sous-triage, sur-triage, réponses dangereuses et latences p50/p95 non établis sur une référence cliniquement validée.

## 7. Décision de poursuite

La poursuite technique est possible dans le périmètre privé et expérimental. La clôture documentaire doit attendre les résultats manquants ; l'usage clinique réel reste hors périmètre et non autorisé.

Étapes restantes : revue des comparaisons, revue et expérimentation DPO, comparaison figée incluant DPO, évaluation finale indépendante, démonstration API avec modèle réel, performances et revue du rapport. Les décisions et preuves doivent rester séparées de toute validation clinique.
