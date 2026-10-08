# Provenance du résultat affiché

Date : 2026-10-08 · Statut : draft
Sources : src/triage_poc/api.py ; src/triage_poc/demo_ui/ ; tests/test_api.py.

La réponse POST /v1/triage expose guardrail_status et guardrail_version provenant du ProviderResult réel. Les motifs internes et la sortie brute ne sont pas exposés. Les valeurs par défaut permettent de lire les anciennes réponses, mais le frontend exige une version de garde-fou renseignée avant d’attribuer une provenance.

L’interface distingue proposition conservée, ajustée et remplacement conservateur. Elle conserve les champs métier, sépare les détails techniques, explique les questions de collecte et respecte l’attribut HTML hidden. Le changement de scénario ou de langue efface le résultat précédent. Les sélecteurs sont bloqués pendant la requête pour éviter une attribution au mauvais scénario.

Validation locale : tests du contrat API pour les trois statuts et absence de motifs internes. Le parcours navigateur est vérifié séparément du calcul GPU et du déploiement. Aucune modification clinique, aucun changement de seuil ni nouveau modèle.
