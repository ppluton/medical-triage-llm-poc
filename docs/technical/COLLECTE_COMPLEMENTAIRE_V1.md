# Parcours de collecte complémentaire

Date : 2026-09-14 — Statut : draft
Sources : ADR-015, src/triage_poc/collection.py, src/triage_poc/api.py, tests/test_collection.py.
Version : API 0.3.0, collecte `explicit-collection-v1-proposed`, prompt `triage-demo-v5-proposed`.

## Utilisation

L'environnement et l'authentification restent ceux de la factory privée vLLM. À chaque `POST /v1/triage`, le client transmet le contexte consolidé et reçoit la proposition du modèle ainsi que `collection`. Aucun stockage de session côté serveur n'est nécessaire. Chaque appel possède son identifiant et sa trace d'audit.

Le client présente les questions de `collection.questions` et écrit chaque réponse dans le champ indiqué par `field`. Il conserve les réponses précédentes et renvoie le contexte complet au prochain appel. Deux questions au maximum sont proposées à la fois, dans l'ordre des rubriques de collecte. Les questions libres produites par le modèle dans `follow_up_questions` restent distinctes ; elles ne constituent pas des champs automatiquement interprétables.

Champs supplémentaires facultatifs : `evolution`, `intensity` (texte), `associated_symptoms`, `vulnerability_factors` (listes de textes). Les champs libres suivent l'anonymisation entrée/sortie et l'audit existants. `confirmed_absent` peut contenir uniquement les noms de champs de liste pour lesquels une absence a été explicitement déclarée ; `unavailable_fields` indique des rubriques que l'opérateur ne peut renseigner. Ces noms sont des énumérations bornées. Une liste vide seule reste inconnue. Une constante `null` n'est pas une mesure.

## Exemple synthétique sur trois appels

Premier contexte, langue `fr` :

```json
{"age_group":"adult","symptoms":["synthetic"]}
```

Les premières questions concernent `duration` et `evolution`. Le client ajoute leurs réponses au contexte ; les questions suivantes concernent `intensity` et `associated_symptoms`.

Après collecte, un contexte de test peut être :

```json
{
  "age_group":"adult",
  "symptoms":["synthetic"],
  "duration":"Synthetic duration",
  "evolution":"Synthetic evolution",
  "intensity":"Synthetic intensity",
  "confirmed_absent":["associated_symptoms","medical_history","allergies","medications","vulnerability_factors"],
  "unavailable_fields":["vitals"]
}
```

`questions` et `pending_fields` sont alors vides ; `unavailable_fields` conserve `vitals`. Il ne faut pas remplir automatiquement `confirmed_absent` pour avancer. Une valeur fournie et marquée indisponible ou absente est refusée (422). Pour corriger une réponse, le client remplace la valeur et retire le statut devenu incompatible.

## Portée de la preuve

L'API continue de demander une évaluation à chaque appel : elle n'attend pas une collecte complète pour restituer une priorité `maximum`. La collecte ne modifie pas la priorité et n'évalue pas la pertinence clinique des valeurs. Toutes les rubriques traitées ne signifient pas « patient stable » ni « triage sûr ».

Tests reproductibles : `PYTHONPATH=src python -m pytest -q tests/test_collection.py tests/test_api.py tests/test_serving.py tests/test_endpoint_evaluation.py`.

Les tests synthétiques avec fournisseur simulé vérifient les tours FR/EN, les contradictions de statut, le suivi des inconnues et le raccord d'anonymisation/audit. Ils ne prouvent pas le comportement du modèle réel avec le prompt v5, ni un parcours rendu dans une interface, ni la pertinence clinique. Une vérification GPU séparée doit mesurer ces limites, sans toucher au test QA figé de v35.
