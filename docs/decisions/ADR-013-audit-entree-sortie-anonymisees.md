# ADR-013 — Audit des entrées et sorties anonymisées

- Date : 2026-09-12
- Statut : proposed — implémentation locale pour satisfaire la spécification
- Propriétaire : porteur du POC
- Statut clinique : not validated
- Sources : SPEC_POC_TRIAGE_MEDICAL.md §9, ADR-010 §5, rapport intermédiaire du 12 septembre.

## Contexte

Le journal limité aux métadonnées ne permet pas de relire une interaction et ne
satisfait pas la spécification. Le mandat exige une entrée anonymisée et une sortie,
avec identifiant, horodatage, versions, statut des contrôles et latence.

## Décision technique proposée

Le fournisseur renvoie une enveloppe par requête : résultat validé, version du
modèle et contexte anonymisé effectivement envoyé au modèle. Il ne conserve pas
le dernier contexte dans un attribut partagé entre requêtes. Les champs textuels
de la sortie passent aussi par l'anonymiseur avant réponse et journalisation.
L'API journalise cette enveloppe avec la réponse délivrée et ses métadonnées.
Les échecs de fournisseur ou d'anonymisation restent sans texte brut. Une erreur
d'écriture du journal empêche la délivrance de la réponse.

Le fichier reste local et privé, hors Git. La démonstration utilise des cas
synthétiques. Aucune durée de conservation clinique n'est inventée : le choix de
stockage, d'accès et de rétention du pilote doit être fixé avec sa cible avant
déploiement. Cette implémentation ne vaut pas autorisation de données patient réelles.

## Alternatives et conséquences

Conserver uniquement des hashes empêcherait la relecture demandée. Conserver les
requêtes brutes exposerait des identifiants et contredirait la minimisation. Une
copie partagée sur le fournisseur risquerait de mélanger les requêtes concurrentes.
L'enveloppe explicite relie chaque trace à son propre contexte, au prix d'un
contrôle d'anonymisation supplémentaire sur les réponses générées.

## Preuve attendue

Un test d'intégration API avec transport modèle simulé doit retrouver dans le
fichier le même identifiant et la même réponse qu'en HTTP, sans l'identifiant
synthétique présent dans l'entrée et la sortie du transport. Un échec de contrôle
de sortie doit empêcher réponse et contenu sensible dans l'audit. Ces tests ne
prouvent ni inférence vLLM réelle ni anonymisation exhaustive par Presidio.
