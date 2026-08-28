# Guide de travail — POC Agent IA de triage médical

## Mission et source de vérité

Ce dépôt contient un projet d'étude public : un Proof of Concept d'assistant IA de triage initial pour le Centre Hospitalier Saint-Aurélien (CHSA). Son objectif est de démontrer une faisabilité technique et une valeur clinique potentielle, sans jamais remplacer le jugement d'un professionnel de santé.

Les exigences de référence sont, dans cet ordre :

1. `CADRAGE_MISSION.md` — mandat, livrables, calendrier et limites de responsabilité.
2. `SPEC_POC_TRIAGE_MEDICAL.md` — exigences fonctionnelles et techniques.
3. Les décisions consignées dans `docs/decisions/` — seulement lorsqu'elles ne contredisent pas les deux documents ci-dessus.

Ne pas présenter le POC comme un dispositif médical, un outil de diagnostic, une prescription, ni une décision clinique autonome. Toute affirmation de performance clinique nécessite un protocole, des données et une validation clinique explicitement documentés.

## Dépôt public : règles non négociables

- Ne jamais versionner de secrets, jetons, variables `.env`, données patient identifiantes, export de logs, poids de modèle volumineux ou cache de dataset.
- Utiliser uniquement des données ouvertes dont la licence, la version, la provenance et les restrictions d'usage ont été vérifiées et consignées.
- Privilégier les scénarios synthétiques pour les démonstrations et les tests. Toute donnée réelle exige une autorisation et une gouvernance hors périmètre de ce dépôt.
- Les exemples cliniques doivent être clairement étiquetés `synthetic` et ne doivent pas permettre de réidentifier une personne.
- Ne jamais inventer un seuil clinique, une règle d'escalade ou une validation médicale. Les consigner comme `proposed` tant qu'un référent clinique ne les a pas approuvés.

## Organisation des documents

Conserver une séparation stricte entre les documents ci-dessous. Les documents professionnels ne doivent pas être dilués par des notes de cours, et les notes d'apprentissage ne sont pas des preuves de fonctionnement.

```text
CADRAGE_MISSION.md                 # mandat fourni, inchangé sauf correction explicitement demandée
SPEC_POC_TRIAGE_MEDICAL.md         # spécification fournie, inchangée sauf correction explicitement demandée
docs/
  README.md                        # index et règles de classement
  learning/                        # notes personnelles pédagogiques, exercices, glossaire
  technical/                       # architecture, contrats, data cards, runbooks, guides reproductibles
  decisions/                       # ADR : décisions, options, conséquences et statut
  evidence/                        # résultats de tests, jeux de tests, métriques et limites
  governance/                      # licences, provenance, anonymisation, analyse de risques
reports/                           # rapport final publiable (maximum 20 pages une fois figé)
data/
  manifests/                       # inventaires, schémas, checksums et cartes de données sans données brutes
  samples/                         # petits exemples synthétiques anonymes et revus
```

Créer les dossiers au besoin, en ajoutant un fichier suivi par Git si leur contenu doit être conservé. Les artefacts reproductibles lourds (jeux bruts, checkpoints, sorties de run) restent hors Git ; versionner plutôt leur manifeste, leur checksum, leur configuration et leur emplacement contrôlé.

## Convention de documentation

- Rédiger la documentation de projet en français, avec termes et identifiants techniques en anglais quand ils sont conventionnels.
- Donner à chaque document un titre, une date, un statut (`draft`, `proposed`, `approved`, `superseded`) et les sources utilisées.
- Une note dans `docs/learning/` explique ce qui a été appris, les hypothèses et les sources ; elle ne fait aucune promesse de performance.
- Un document dans `docs/technical/` décrit ce qui est implémenté ou reproductible : version, prérequis, commande, entrée, sortie et limites.
- Une entrée dans `docs/evidence/` sépare clairement : mesure observée, environnement, version de code/modèle/données, commande exécutée, résultat et limite de la preuve.
- Les décisions structurantes utilisent `docs/decisions/ADR-XXX-titre-court.md` et indiquent contexte, décision, alternatives, conséquences, propriétaire et statut clinique.
- Avant publication, retirer toute information sensible et vérifier les liens, licences, chiffres, commandes et affirmations.

## Suivi pédagogique de chaque étape majeure

Pour chaque étape majeure du projet, créer deux traces complémentaires avant de passer à l'étape suivante :

1. Une note pédagogique dans `docs/learning/` qui répond clairement à : **ce qui a été fait**, **pourquoi cela était nécessaire**, **comment cela a été réalisé**, les notions à retenir, les hypothèses et les questions encore ouvertes.
2. Une note professionnelle dans `docs/technical/`, `docs/governance/`, `docs/decisions/` ou `docs/evidence/` selon sa nature. Elle doit être factuelle, reproductible et séparer l'implémentation, le résultat mesuré et les limites de la preuve.

Pour toute preuve ou décision significative, compléter la trace par :

- le périmètre et la question traitée ;
- les entrées, outils, versions et commandes utilisées ;
- le résultat observé ;
- ce que ce résultat prouve et ne prouve pas ;
- la prochaine décision ou l'étape suivante.

Les grandes étapes couvertes par ce suivi sont : gouvernance des sources, préparation et anonymisation des données, baseline, SFT/LoRA, DPO, évaluation de sûreté, API et audit, CI/CD et déploiement pilote, puis rapport final. Une note d'apprentissage n'est jamais substituable à une preuve technique ou clinique.

## Démarche de réalisation

Travailler par incréments vérifiables, sans sauter directement à l'entraînement complet :

1. Établir l'inventaire des sources, leurs licences et leur data card.
2. Définir le schéma canonique SFT/DPO, les splits et le journal de transformations.
3. Mettre en place l'anonymisation, ses tests et la revue d'échantillons synthétiques.
4. Construire une baseline reproductible, puis SFT/LoRA, puis DPO, avec les mêmes jeux d'évaluation isolés.
5. Implémenter l'API et ses garde-fous avant une exposition pilote.
6. Mesurer la qualité, les cas dangereux, la latence et la traçabilité ; documenter les résultats négatifs aussi.
7. Rédiger le rapport à partir des preuves versionnées, jamais à partir d'estimations non mesurées.

Chaque étape doit produire au minimum une note technique ou de gouvernance, une configuration versionnée et une preuve adaptée. Si un choix dépasse la spécification (taxonomie de risques, seuils d'acceptation, politique de conservation), le proposer dans un ADR avant de le coder.

## Données, modèle et évaluation

- Préserver l'isolement strict des jeux `train`, `validation` et `test`. Ne jamais ajuster un modèle à partir des résultats du jeu de test.
- Chaque enregistrement transformé doit pouvoir être relié à sa source, licence, transformation, statut d'anonymisation et split.
- Fixer et journaliser les versions de données, le hash de code, la seed, les hyperparamètres, le prompt, les garde-fous et le checkpoint pour chaque run.
- Comparer explicitement base, SFT et DPO sur un protocole identique. Ne pas conclure à un gain sans mesure comparable.
- Tester au minimum les scénarios spécifiés : douleur thoracique, détresse respiratoire, déficit neurologique, pédiatrie, grossesse, vulnérabilité, informations insuffisantes ou contradictoires, et français/anglais.
- Distinguer les résultats automatiques, la revue humaine et la validation clinique. Seule cette dernière peut étayer une affirmation de pertinence clinique.

## API et sécurité du POC

L'API cible `POST /v1/triage` doit valider son schéma, normaliser les entrées, retourner uniquement les trois niveaux `maximum`, `moderate` ou `deferred`, inclure l'avertissement de sécurité requis et fournir un identifiant d'interaction.

Les garde-fous doivent privilégier l'escalade vers un professionnel lorsque le contexte est incomplet, contradictoire ou comporte un signal d'alerte. Les journaux d'audit minimisent les données, contiennent des entrées anonymisées et enregistrent les versions du modèle, prompt et contrôles. Les identifiants et secrets de déploiement ne sont jamais loggés.

## Tests et niveau de preuve

Avant de dire qu'un comportement fonctionne, formuler le claim utilisateur exact et conserver la preuve la plus directe disponible. Distinguer toujours :

- code écrit ou revue statique ;
- tests unitaires et de schéma ;
- test d'intégration FastAPI ;
- exécution d'inférence ;
- mesure de performance ;
- revue clinique ;
- exposition pilote ou production.

Un test vert, une réponse HTTP 200 ou un conteneur construit ne prouve ni la sûreté clinique, ni la qualité du triage, ni une intégration hospitalière réelle. Les régressions, erreurs et résultats non concluants sont documentés dans `docs/evidence/`.

## Git et livrables

- Garder les commits petits, atomiques et conventionnels : `docs(scope): ...`, `feat(api): ...`, `test(safety): ...`.
- Ajouter et vérifier les chemins explicitement ; préserver tout travail non lié déjà présent dans l'arbre.
- Avant une publication GitHub, relire le diff comme un document public : données, secrets, licences, formulations médicales, fichiers lourds et résultats non prouvés.
- Ne déployer ou ne publier aucun endpoint, modèle, dataset, container ou artefact externe sans cible et autorisation explicites.

## Attitude pédagogique attendue

Expliquer les choix au fil du projet dans `docs/learning/`, puis les traduire en décisions et artefacts techniques dans les emplacements dédiés. L'objectif est de pouvoir montrer simultanément : ce qui a été appris, ce qui a réellement été construit, et ce qui reste à faire valider par des professionnels de santé.
