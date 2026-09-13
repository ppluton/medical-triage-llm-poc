# Mesurer l'endpoint de démonstration

- Date : 2026-09-12
- Statut : draft — runner implémenté et testé avec transport simulé ; aucune mesure cloud
- Sources : [runner](../../scripts/evaluate_triage_endpoint.py), [tests](../../tests/test_endpoint_evaluation.py), [scénarios proposés](../../data/samples/synthetic-triage-development-v2.json).

## Entrées et exécution

Utiliser l'environnement Python du projet avec `PYTHONPATH=src`. L'endpoint doit déjà être servi sur une cible autorisée. `TRIAGE_API_TOKEN` est fourni dans l'environnement, jamais sur la ligne de commande ni dans le rapport.

```sh
PYTHONPATH=src python scripts/evaluate_triage_endpoint.py \
  --url https://endpoint-prive-autorise.example \
  --scenarios data/samples/synthetic-triage-development-v2.json \
  --output artifacts/endpoint-evaluation/run-001.json
```

L'URL ci-dessus est un placeholder, pas un déploiement. Seuls HTTPS et HTTP local sont acceptés, sans identifiants dans l'URL. Le runner refuse les jeux non explicitement synthétiques et l'écrasement d'un rapport existant.

## Sorties et limites

Le runner appelle `POST /v1/triage` pour chaque scénario. Il vérifie le contrat de réponse, l'identifiant UUID unique, la version du modèle et la présence d'un avertissement. Il conserve les erreurs HTTP/transport/schéma dans le dénominateur et retourne un code non nul si une requête échoue. Les corps d'erreur et exceptions réseau ne sont pas publiés dans le rapport.

Les p50/p95 portent sur les latences observées côté client de toutes les requêtes, succès et échecs, en série, démarrage à froid inclus ; calcul par rang le plus proche. Ce n'est ni un test de charge concurrente ni un score de qualité médicale. Les identifiants reçus devront être rapprochés des vrais logs serveur pour prouver leur persistance.

Deux tests avec transport simulé passent : comptabilisation d'un échec HTTP et d'un UUID réutilisé ; refus de données non marquées avant tout appel. Ruff passe. Cela valide le runner local, pas le serveur, vLLM ou le déploiement cloud. Aucun endpoint externe n'a été appelé dans cette étape.

## Rapprocher les réponses et l'audit

Après récupération autorisée du journal privé de la même exécution, utiliser :

```sh
PYTHONPATH=src python scripts/verify_endpoint_audit.py \
  --report artifacts/endpoint-evaluation/run-001.json \
  --audit /chemin/prive/audit.jsonl \
  --output artifacts/endpoint-evaluation/audit-001.json
```

Le contrôle exige une seule entrée par réponse réussie, l'égalité intégrale de la
réponse avec la sortie auditée, les versions de prompt/contrôles et la présence de
l'entrée anonymisée avec statut de confidentialité `passed`. Il refuse un lot sans
réponse réussie. Les requêtes HTTP échouées restent comptées séparément ; un rapprochement
réussi ne les transforme pas en succès. Le résultat contient des empreintes des deux
fichiers et des motifs de divergence, sans recopier le contenu de l'audit.

Cela prouve la correspondance avec l'export fourni. La persistance durable sur le vrai
serveur, la rétention et l'efficacité de l'anonymisation restent des preuves distinctes.

## Débit séquentiel — 2026-09-13

Le rapport inclut maintenant `elapsed_seconds`, `requests_per_second`,
`successful_responses_per_second` et `concurrency: 1`. Le temps total couvre
la boucle entière, y compris le traitement des réponses ; les échecs comptent
dans le débit des requêtes mais pas dans celui des réponses réussies.
Le test à horloge contrôlée vérifie 3 requêtes en 12 secondes, dont une réussie :
0,25 requête/s et 0,08333 réponse réussie/s. Ces chiffres sont une fixture de test,
pas une mesure du modèle. Les deux tests ciblés passent et Ruff passe.
L'horloge simulée est isolée du transport HTTP ; un premier essai de test a révélé
qu'un remplacement global de l'horloge affectait aussi httpx, puis a été corrigé.
La capacité sous concurrence reste à mesurer sur le service réel.
