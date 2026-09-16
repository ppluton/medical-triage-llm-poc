# Garde-fous déterministes de restitution — v1

- Date : 2026-09-16
- Statut : proposed, implémenté et vérifié localement
- Versions : API `0.4.0`, prompt `triage-demo-v6-proposed`, contrôles `proposed-guardrails-v1`
- Sources : [ADR-016](../decisions/ADR-016-portes-surete-etape-2.md),
  [évaluation v36](../evidence/STAGE2_SAFETY_V36_RESULT_2026-09-16.md),
  `src/triage_poc/guardrails.py`, `src/triage_poc/serving.py`.
- Statut clinique : aucune validation clinique ; règles conservatrices proposées pour le POC.

## Objectif et position dans la chaîne

Le modèle reste chargé de proposer une réponse structurée, mais sa sortie n'est plus
restituée automatiquement après la seule validation JSON. La chaîne applique maintenant,
dans cet ordre : anonymisation ciblée, génération contrainte, validation Pydantic,
nettoyage de sortie, garde-fous déterministes, réponse API et audit.

Ces contrôles visent les défauts effectivement observés en v36. Ils ne constituent ni un
système expert complet, ni une preuve de sûreté clinique.

## Politique d'anonymisation de service

La politique de service masque les noms explicitement introduits comme noms de patient,
les téléphones, courriels, cartes, IBAN, adresses IP et références patient. Les entités
génériques `PERSON`, `LOCATION` et `DATE_TIME` restent utilisées pour l'audit de corpus,
mais ne sont plus masquées aveuglément dans l'API : Presidio avait interprété des durées
cliniques comme des dates et détruisait une information utile.

Cette séparation réduit le faux positif observé ; elle ne garantit pas l'absence de tout
identifiant dans un texte libre. Le service échoue toujours fermé lorsque l'analyse ou la
réanalyse ne peut pas être effectuée.

## Décisions possibles

Le résultat du garde-fou possède trois états d'audit :

- `model_output` : aucune signature bornée n'a déclenché de correction ;
- `corrected` : la sortie est conservée, mais la priorité minimale ou les signaux d'alerte
  sont corrigés à partir d'informations explicitement présentes dans l'entrée ;
- `safe_fallback` : une affirmation non étayée ou une corruption connue remplace toute la
  sortie par un message conservateur.

Le niveau minimal `maximum` est appliqué uniquement aux formulations bornées de signaux
d'alerte proposées dans le prompt : douleur thoracique intense persistante, difficulté
respiratoire sévère, déficit neurologique focal soudain, altération de conscience ou
aggravation sévère explicite. L'incertitude, la contradiction, la grossesse ou une
vulnérabilité explicite imposent au minimum `moderate`. Ces règles sont des choix de POC à
faire revoir, pas des seuils médicaux approuvés.

## Signatures refusées

Le remplacement conservateur est déclenché par une liste limitée de signatures :

- constantes ou stabilité affirmées sans données correspondantes ;
- absence de symptômes, antécédents ou médicaments déduite d'un champ inconnu ;
- placeholder de confidentialité, entité HTML ou nom de champ rendu comme contenu ;
- répétition exacte d'un bloc de six mots ;
- longue chaîne vraisemblablement tronquée.

Une absence de déclenchement ne signifie donc pas que tout le contenu est fondé. Ajouter
une nouvelle signature nécessite un exemple reproductible et un test de non-régression.

## Traçabilité et reprise

L'audit enregistre `guardrail_status`, `guardrail_version`, `guardrail_reasons`, le modèle,
le prompt et `controls_version=schema-privacy-collection-guardrails-v5`. Les motifs sont des
codes bornés et ne recopient pas le texte patient. La réponse publique ne dévoile pas ces
détails internes.

Le prompt v6 augmente modérément les limites des champs et exige des éléments complets,
sans entités HTML ni placeholders. Une terminaison vLLM autre que `stop` reste une erreur ;
le garde-fou ne transforme pas une génération incomplète en succès silencieux.

## Vérification et limites

Les tests ciblés couvrent les priorités minimales, le remplacement conservateur,
l'anonymisation FR/EN, l'audit et le replay. Le [replay v36](../evidence/STAGE2_GUARDRAIL_REPLAY_V36_2026-09-16.md)
montre le comportement sur les sorties sauvegardées, sans nouvelle inférence.

Une prochaine preuve GPU doit exécuter Base, SFT et DPO avec ce code, vérifier les audits,
mesurer les activations de fallback et refaire une revue de contenu. Un nouveau jeu final
aveugle et une revue clinique indépendante restent nécessaires avant toute affirmation de
sûreté ou de pertinence clinique.
