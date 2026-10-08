# Provenance du résultat affiché

Date : 2026-10-08 · Statut : draft
Sources : src/triage_poc/api.py ; src/triage_poc/demo_ui/ ; tests/test_api.py.

La réponse POST /v1/triage expose guardrail_status et guardrail_version provenant du ProviderResult réel. Les codes de motifs connus sont exposés par liste blanche ; les messages internes arbitraires restent exclus. La sortie brute des tokens n’est pas exposée. Les valeurs par défaut permettent de lire les anciennes réponses, mais le frontend exige une version de garde-fou renseignée avant d’attribuer une provenance.

L’interface distingue proposition conservée, ajustée et remplacement conservateur. Elle conserve les champs métier, sépare les détails techniques, explique les questions de collecte et respecte l’attribut HTML hidden. Le changement de scénario ou de langue efface le résultat précédent. Les sélecteurs sont bloqués pendant la requête pour éviter une attribution au mauvais scénario.

Validation locale : tests du contrat API pour les trois statuts et exclusion des motifs internes inconnus. Le parcours navigateur est vérifié séparément du calcul GPU et du déploiement. Aucune modification clinique, aucun changement de seuil ni nouveau modèle.

## Inspection pédagogique et contrat FastAPI

La requête peut inclure `include_model_proposal: true` (false par défaut). La réponse
ajoute alors `model_proposal`, après validation du schéma et filtrage de confidentialité,
mais avant les garde-fous de contenu. Cette proposition ne constitue pas une recommandation
validée ; elle est retirée de la sortie conservée dans l’audit. Le frontend la demande
pour sa démonstration synthétique, dans une section repliable distincte du résultat final.
Les raisons réelles sont affichées, y compris le remplacement systématique lorsque
`explicit_proposed_warning_sign` est déclenché. Ce cas ne prouve pas une erreur du modèle.

L’inspecteur affiche le corps JSON réellement envoyé et reçu lors du dernier succès.
Il n’affiche aucun en-tête d’authentification. Le changement de contexte masque le résultat.
Ne saisir que des scénarios synthétiques : le corps de requête représente la saisie locale.

`/docs/` sur Cloudflare Pages présente Swagger en lecture seule, avec ses assets locaux
et le schéma `deploy/cloudflare_pages/static/docs/openapi.json`. Celui-ci est généré
par `create_app().openapi()` et un test compare son contenu à l’application courante.
Le formulaire sécurisé permet d’exécuter l’appel réel. Le endpoint health du schéma
est celui du backend (`/healthz`) ; le proxy public utilise `/v1/healthz`.

Contrôles : 256 tests Python, Ruff, build Pages, rendu navigateur local avec provider
synthétique, confidentialité de la proposition et non-persistance dans l’audit.
La preuve du service GPU public est distincte de ces contrôles locaux.
