# Retour pédagogique sur la démarche du projet

- **Date :** 2026-09-11
- **Statut :** draft
- **Périmètre :** questions, hypothèses et enseignements documentés depuis le cadrage jusqu'au pilote Kaggle v18.
- **Sources :** [historique professionnel](../technical/HISTORIQUE_PROJET_2026-09-11.md), documents de preuve et décisions qui y sont référencés, [audit final](../evidence/SFT_V2_READINESS_2026-09-11.md).

Cette note explique les choix et leurs révisions. Elle ne reconstitue pas une transcription exhaustive des conversations et ne constitue pas une validation médicale.

## 1. Ce que nous essayons d'apprendre au modèle

Le projet final est un assistant de triage initial. Pourtant, les sources ouvertes retenues contiennent surtout des questions et réponses médicales. Cette distinction est fondamentale : apprendre à répondre à une question médicale ne suffit pas à apprendre une priorité de triage fiable.

Nous avons donc séparé l'adaptation aux QA médicales, l'évaluation sur des scénarios de triage synthétiques et les garde-fous de l'API. Nous n'avons pas inventé de labels de gravité pour transformer artificiellement chaque QA en décision clinique. Il reste à mesurer si cette adaptation aide réellement la tâche finale.

## 2. Pourquoi la préparation des données a pris autant de place

Un fichier téléchargeable peut contenir des réponses vides, des doublons, des restrictions d'usage ou des exemples incomplets après transformation. Une même vignette peut aussi apparaître sous plusieurs questions : séparer simplement les identifiants de lignes ne suffit alors pas à séparer entraînement et évaluation.

Nous avons successivement vérifié les sources et leurs licences, corrigé l'identification de MediQAl, reconstruit les exemples et contrôlé leur provenance. Les scénarios synthétiques préparés au début constituent un lot distinct ; le premier SFT Kaggle a utilisé des QA issues des sources ouvertes.

Lors de la reprise du pipeline, nous avons découvert des QCM sans toutes leurs propositions et des réponses tronquées. Le corpus v2 corrige ces transformations. Un audit plus fin a ensuite révélé des groupes documentaires communs entre splits. Le corpus revu conserve **3 721 exemples train, 479 validation et 500 test** après exclusions, sans déplacer les exemples réservés vers le train.

Trois QCM comportant des propositions dupliquées ont été exclus plutôt que corrigés médicalement sans autorité. Les exemples de développement ont été comparés aux sources : 4 195 correspondances exactes et cinq correspondances après rejeu exact de l'anonymisation.

**À retenir :** « propre » doit toujours préciser le contrôle réalisé. Ces vérifications étayent la fidélité des transformations et l'isolation selon les clés définies. Elles ne certifient ni l'exactitude médicale de chaque réponse source, ni l'absence de toute proximité sémantique, ni une anonymisation universelle.

## 3. Ce que le premier SFT nous a appris

Le premier entraînement complet a terminé ses 1 000 étapes et produit des poids sauvegardés. C'est une réussite technique réelle : la chaîne GPU pouvait apprendre et exporter un adaptateur.

La comparaison suivante a montré une loss plus faible sur les réponses de validation. Mais les générations ont révélé un défaut majeur : les 30 réponses SFT observées atteignaient la limite de 256 tokens. Certaines étaient répétitives ou dérivaient de langue.

La **loss** mesure à quel point le modèle attribue de la probabilité aux tokens de la réponse attendue lorsqu'on lui fournit les tokens précédents. Lors d'une **génération**, il doit continuer à partir de ses propres choix. Il peut donc mieux prédire une référence tout en produisant une réponse libre dégradée.

**Changement de méthode :** vérifier ensemble la loss, les réponses réellement générées, la terminaison et les répétitions. Ne pas conclure à la qualité à partir de la seule courbe d'entraînement.

## 4. Comment nous avons réduit les hypothèses

Les essais suivants ont examiné plusieurs explications : token de fin, quantification, moteur de chargement et construction des labels. Certains essais ont été bloqués par l'infrastructure Kaggle, notamment l'attachement automatique de la dernière sortie au lieu des poids historiques recherchés. Ces incidents n'étaient pas des résultats sur le modèle.

L'audit des labels a montré que le format initial n'entraînait pas le token de fin natif attendu. Nous avons ensuite testé de petites continuations, puis une loss limitée à la réponse. Les micro-runs v15 à v17 ont obtenu une terminaison sur les trois exemples observés, avec des sorties identiques après recharge de leurs adaptateurs.

Cela étaye la mécanique dans ces essais, mais n'isole pas parfaitement une cause unique : plusieurs paramètres ont évolué et il manquait certains contrôles. Nous conservons cette limite au lieu d'affirmer que le token de fin expliquait tout.

## 5. Pourquoi deux QCM incorrects ne condamnaient pas le projet

Deux réponses restaient incorrectes par rapport aux références après les micro-runs. L'observation devait être conservée, mais elle ne permettait pas de conclure que tout le corpus était faux ou que le prochain SFT complet échouerait.

Ces essais ne comportaient que 20 étapes, sur un petit lot, depuis l'ancien adaptateur. Leur objet était surtout de vérifier des mécanismes. Inversement, trois réponses qui s'arrêtent correctement ne prouvent pas une amélioration générale.

La question utile est devenue : **pouvons-nous observer un signal d'apprentissage et une génération exploitable sur un protocole fixé, avant d'engager plusieurs heures supplémentaires ?** L'objection de l'utilisateur au lancement prématuré d'un entraînement de quatre heures a conduit au pilote borné.

## 6. Ce qui a été vérifié avant le pilote

Le contrôle a été poussé jusqu'au trainer réel : les prompts doivent être masqués dans la loss, les réponses conservées, le token de fin présent une fois et aucun exemple ne doit être tronqué par la longueur maximale. Les 4 200 exemples train/validation passent ces contrôles ; le test reste réservé.

Un modèle minuscule sur CPU a également servi à comparer un entraînement continu et une interruption suivie d'une reprise. Ce test vérifie un contrat logiciel précis ; il ne reproduit pas toute la pile GPU Unsloth, ses types numériques et ses optimisations.

Cette distinction s'est révélée concrète lors du pilote : les contrôles de labels et la baseline ont abouti sur GPU, mais le démarrage de l'optimisation a rencontré une erreur FP16. Les tests CPU ne permettaient pas de prouver ce comportement matériel.

## 7. Le pilote v18 et son résultat à cette date

Le pilote repart de la base avec un nouvel adaptateur. Son budget d'entraînement est limité à 150 étapes ou 1 800 secondes ; les évaluations et la préparation sont supplémentaires. Il compare les mêmes 479 références et 30 générations fixées à l'avance, équilibrées entre français et anglais.

**Résultat observé :** la baseline a été sauvegardée, puis l'exécution a échoué au premier passage d'optimisation avec `ValueError: Attempting to unscale FP16 gradients.` Aucun résultat SFT du pilote n'est disponible. La cause racine doit encore être vérifiée dans le chemin de préparation du modèle et des paramètres entraînables.

Cet incident appartient à la mécanique numérique de l'entraînement. Il ne constitue pas une mesure de la qualité du corpus. Il justifie de vérifier cette mécanique avec un essai court avant de relancer le budget pilote ; aucun SFT long n'est approuvé par ce résultat.

## 8. Pourquoi le DPO vient ensuite

Le SFT apprend à reproduire une réponse cible. Le DPO utilise des paires de réponses préférée/rejetée pour ajuster les préférences du modèle. Il faut donc un SFT de référence mesuré et des préférences correctement préparées.

Le DPO ne répare pas automatiquement un mauvais format, une fuite entre splits ou des exemples corrompus. Le premier lot préparé a d'ailleurs été rejeté parce que l'anonymisation supprimait des notions médicales. Le lot suivant reste candidat et nécessite une revue ; aucun DPO n'a encore été entraîné.

La comparaison finale devra utiliser un protocole identique pour Base, SFT et DPO. La validation sert aux décisions intermédiaires ; le test réservé ne doit pas devenir un outil de réglage répétitif.

## 9. Les notions à retenir

| Notion | Sens dans ce projet |
|---|---|
| SFT | Apprentissage supervisé à partir de réponses cibles |
| LoRA | Petit ensemble de paramètres entraînables ajouté au modèle |
| EOS | Token signalant la fin d'une réponse |
| Labels masqués | Tokens du prompt exclus du calcul de loss |
| Validation | Exemples réservés aux comparaisons et décisions de développement |
| Test | Évaluation finale isolée des réglages |
| Checkpoint | Sauvegarde des poids et, pour reprendre, de l'état d'entraînement |
| Recharge | Charger les poids et reproduire une inférence |
| Reprise | Continuer avec optimiseur, scheduler et états aléatoires conservés |
| DPO | Ajustement à partir de préférences entre deux réponses |
| Preuve clinique | Validation selon un protocole et par les personnes compétentes ; absente ici |

## 10. La suite, dans l'ordre

1. Diagnostiquer et vérifier le défaut FP16 du pilote avec une exécution courte.
2. Obtenir une comparaison Base/Pilote exploitable et examiner les réponses, pas seulement les métriques.
3. Vérifier la recharge et la reprise sur la pile GPU réelle avant toute prolongation.
4. Décider d'une poursuite SFT à partir de ces preuves, puis préparer et tester le DPO.
5. Comparer Base/SFT/DPO, intégrer le vrai modèle à l'API et mesurer les garde-fous et la latence.
6. Finaliser la démonstration autorisée et le rapport à partir des résultats, y compris négatifs.

Le détail chronologique, les chiffres historiques et leurs sources sont regroupés dans l'[historique professionnel](../technical/HISTORIQUE_PROJET_2026-09-11.md). Chaque conclusion doit rester rattachée à son environnement et à son niveau de preuve.
