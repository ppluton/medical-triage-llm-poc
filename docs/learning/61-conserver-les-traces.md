# Conserver les traces quand l'API redémarre

Date : 2026-09-14 — Statut : draft
Sources : ADR-013 ; src/triage_poc/serving.py ; tests/test_audit_restart.py.

Une réponse affichée et une trace durable sont deux résultats différents. Le fichier JSONL existant conservait déjà les lignes entre deux ouvertures ; nous avons ajouté une synchronisation explicite du fichier avant de délivrer l'évaluation. Si le système signale un échec de cette synchronisation, l'API répond « audit indisponible » au lieu de livrer la proposition.

Le test démarre deux processus indépendants. Chacun crée son instance d'API, traite un échange synthétique, puis s'arrête. Nous vérifions ensuite que les deux réponses sont présentes, intactes et avec des identifiants distincts dans le même journal. Le fournisseur du modèle est simulé : ce test traite la persistance locale, pas la qualité du triage.

Cette vérification ne simule pas une panne électrique, une corruption du disque ou la perte du volume d'un hébergeur. Une confirmation du système d'exploitation n'est pas une sauvegarde. Une erreur de synchronisation peut aussi laisser une ligne dans le fichier alors que la réponse HTTP a été refusée ; le journal n'est donc pas une preuve de réception par le client.

Le choix de la durée de conservation et du stockage distant dépend toujours de la cible de démonstration autorisée. Aucun effacement automatique ni hébergement supplémentaire n'a été ajouté.
