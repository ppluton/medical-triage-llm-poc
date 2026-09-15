# Rendre une interaction auditable sans conserver l'entrée brute

- Date : 2026-09-12
- Statut : draft
- Sources : [spécification](../../SPEC_POC_TRIAGE_MEDICAL.md), [preuve locale](../evidence/API_AUDIT_CONTENT_2026-09-12.md).

## Ce qui a été fait et pourquoi

Notre journal disait quand une requête avait eu lieu, mais ne permettait pas de
relire ce que le modèle avait reçu ni répondu. La mission demande cette possibilité.
Nous conservons désormais le contexte déjà anonymisé et la réponse correspondante.

Un test a aussi montré qu'un modèle pouvait écrire un identifiant dans sa sortie,
même si l'entrée avait été nettoyée. Nous appliquons donc le contrôle aux textes de
sortie avant de les renvoyer et de les conserver. Si ce contrôle ou l'écriture
échoue, l'API ne délivre pas l'évaluation.

## Comment et notions à retenir

Chaque appel transporte sa propre enveloppe résultat/version/contexte. Stocker le
« dernier contexte » sur un objet partagé aurait risqué de mélanger des utilisateurs
concurrents. Le fichier contient l'identifiant présent dans la réponse HTTP : cela
permet de relier les deux traces.

Le test utilise un modèle simulé et un masquage déterministe. Il prouve le passage
correct des informations et des erreurs, pas que tous les identifiants réels seraient
reconnus. La durée de conservation et l'hébergement restent à définir avant pilote ;
les démonstrations restent synthétiques et aucune validation clinique n'est acquise.
