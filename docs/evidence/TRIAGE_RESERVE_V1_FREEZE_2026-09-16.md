# Gel de la réserve de triage synthétique v1

- Date : 2026-09-16
- Statut : gelée, non évaluée
- Manifeste : [synthetic-triage-held-out-reserve-v1](../../data/manifests/synthetic-triage-held-out-reserve-v1.json)
- Scénarios : [réserve synthétique](../../data/samples/synthetic-triage-held-out-reserve-v1.json)
- Statut clinique : références proposées, aucune validation clinique

## Objet

Les 18 scénarios v2 ont déjà servi au développement des prompts et garde-fous. Ils ne
peuvent plus étayer une mesure finale indépendante. Cette réserve distincte est figée avant
la lecture des résultats du nouveau SFT et avant tout DPO associé.

## Composition

La réserve contient 18 scénarios synthétiques : neuf français et neuf anglais, deux pour
chacune des neuf familles exigées. Les niveaux proposés sont huit `maximum`, huit `moderate`
et deux `deferred`. Chaque requête valide le contrat Pydantic réel de `POST /v1/triage`.

Le gel vérifie : identifiants uniques et réservés, catégories exactes, équilibre linguistique,
références `proposed_educational_only`, requêtes uniques et absence de recouvrement exact
d'identifiant ou de requête canonique avec le jeu de développement v2.

## Politique d'utilisation

La réserve ne doit influencer ni prompt, ni garde-fou, ni checkpoint, ni hyperparamètre.
Elle sera ouverte une seule fois après sélection du SFT et achèvement du DPO. Toute correction
motivée par son résultat lui retire le statut de réserve finale et impose un nouveau jeu.

## Limites

L'absence de recouvrement exact n'exclut pas les paraphrases ou ressemblances sémantiques.
Les niveaux sont des références prudentes proposées pour le POC, pas des seuils cliniques.
Le gel prouve l'isolation du protocole, pas la sûreté d'un modèle.
