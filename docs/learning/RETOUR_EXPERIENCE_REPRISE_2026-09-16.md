# Apprendre de la première réalisation

Date : 2026-09-16 — Statut : draft
Sources : [audit initial](../evidence/PIPELINE_AUDIT_2026-09-05.md), [audit corrigé](../evidence/SFT_V2_READINESS_2026-09-11.md), [DPO](../evidence/DPO_V27_RESULT_2026-09-13.md), [QA finale](../evidence/FINAL_QA_V35_RESULT.md), [API v34](../evidence/VLLM_API_V34_RESULT.md), mission et livrables OpenClassrooms relus le 16 septembre.

## Ce qui a été fait et pourquoi reprendre

La chaîne a préparé des données, entraîné un SFT puis un DPO et exécuté de vraies inférences. Elle a aussi accumulé des corrections et des documents au point de rendre le parcours difficile à suivre. La reprise repart des attentes de la mission en conservant ces résultats comme preuves datées.

| Constat | Ce que nous apprenons | Correction de méthode |
|---|---|---|
| 2 249/2 250 QCM de développement incomplets et 101 réponses tronquées dans le premier corpus | Un schéma valide ne garantit pas un exemple fidèle | Comparer source et texte réellement rendu au modèle avant entraînement |
| Absence du signal de fin attendu dans le premier rendu | Le contenu et la tokenisation se contrôlent séparément | Vérifier le collateur réel, les labels, le terminateur et la recharge |
| Corrections ultérieures déjà mesurées | Repartir proprement ne signifie pas que tout le travail précédent est faux | Réutiliser les composants identifiés, en vérifiant leur périmètre |
| SFT : loss finale 1,575 → 0,844 ; DPO ≈0,843 | La probabilité d’une réponse de référence ne mesure pas la justesse du triage | Séparer métriques QA, format et comportement métier |
| API v34 : 18/18 formats valides, 8/18 priorités proposées, jamais moderate | Un format correct peut contenir une décision inadéquate | Regarder les trois classes, les erreurs et les différences de langue |
| DPO : 426 paires train en anglais, 20 étapes | Exposition limitée et couverture du besoin à examiner | Revoir les préférences avant de décider d’allonger ; aucune cause unique prouvée |
| Questions manquantes traitées ensuite par suivi déterministe | Une application peut améliorer la collecte sans que le modèle l’ait apprise | Montrer séparément ce que fait le code et ce que fait le modèle |
| Plusieurs guides et phases présentés comme actuels | Une accumulation de traces ne constitue pas un plan lisible | Une seule entrée active ; historique conservé à part |
| API locale GPU et CI de tests disponibles, endpoint extérieur/CD absents | Une preuve partielle ne vaut pas livraison | Anticiper l’hébergement et vérifier depuis l’extérieur |

## Ce qu’il ne faut pas conclure

Les sources de l’école ne sont pas responsables de nos erreurs de conversion. Leur usage reste prévu par la mission. Un corpus QA médical et UltraMedical peuvent servir la spécialisation demandée ; leur présence ne suffit pas à démontrer l’apprentissage du triage bilingue. Générer des priorités sans protocole ni revue ne résoudrait pas cette limite.

Les causes du faible effet DPO restent des hypothèses : durée, sélection des paires, langue et adéquation à l’évaluation. Nous n’avons pas isolé leurs effets. Nous n’avons pas de preuve que les autres étudiants utilisent le même protocole ou obtiennent de meilleurs résultats comparables.

## Organisation retenue

Suivre le [guide actif](../../GUIDE_REPRISE.md). À chaque étape : ce que l’on veut vérifier, l’entrée exacte, la vérification minimale utile, le résultat et la décision suivante. Conserver une note pédagogique et une preuve professionnelle ; réutiliser les documents existants plutôt que multiplier les variantes.

Questions ouvertes : qualité et couverture du corpus à reprendre ; justification clinique des préférences ; cible GPU/coût ; cible d’endpoint ; heure exacte de remise. Une échéance courte impose de limiter les essais, pas de masquer ces questions.
