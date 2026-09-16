# ADR-015 — Suivre les informations de collecte explicitement

Date : 2026-09-14 — Statut : proposed
Propriétaire : projet pédagogique CHSA ; statut clinique : non validé.
Sources : SPEC_POC_TRIAGE_MEDICAL.md, sections 2, 3 et 8 ; docs/evidence/VLLM_API_V34_RESULT.md.

## Contexte et décision

Les réponses v34 omettent les questions sur les contextes incomplets. L'API ne représente pas l'évolution, l'intensité, les symptômes associés ni les facteurs de vulnérabilité ; une liste vide ne distingue pas absence déclarée et information inconnue.

Étendre le contexte avec ces champs facultatifs et deux listes de noms de champs : `confirmed_absent` pour les absences explicitement déclarées dans les champs de type liste, `unavailable_fields` pour les informations que l'opérateur ne peut pas obtenir. Refuser les états contradictoires. Ne jamais inférer une absence à partir d'une liste vide.

Ajouter à la réponse API un objet `collection` calculé par l'application : champs restant à renseigner, champs indisponibles et au plus deux questions FR/EN liées à des champs. À chaque appel, le client renvoie le contexte consolidé ; les champs renseignés ou indisponibles ne sont plus demandés. Les questions libres du modèle restent séparées. Le contexte enrichi et la réponse sont anonymisés et audités dans le flux existant.

## Portée et alternatives

Ce mécanisme organise la collecte prévue au mandat ; il ne sélectionne aucune priorité et ne définit aucun seuil médical. L'inférence reste possible à chaque appel : la collecte ne constitue pas une condition préalable à une évaluation urgente. `pending_fields` vide signifie uniquement que chaque rubrique a été traitée ou déclarée indisponible, jamais que le contexte est suffisant cliniquement.

L'alternative consistant à dépendre exclusivement des questions du modèle n'est pas retenue compte tenu de v34. Une session serveur persistante n'est pas nécessaire pour ce POC : le client conserve le contexte, et chaque appel garde son identifiant d'audit distinct. La pertinence clinique des questions, la détection des contradictions dans le texte et les contrôles d'escalade restent à vérifier séparément. Aucun résultat de test réservé ne motive cette modification.
