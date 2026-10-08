# Lire le résultat de la démonstration

Date : 2026-10-08 · Statut : draft
Sources : api.py, demo_ui/app.js, guardrails.py et collection.py.

Le frontend affiche le résultat final après contrôles. Le statut conservé, corrigé ou remplacé explique l’intervention des garde-fous. Il ne prouve pas la qualité clinique. Les questions de collecte suivent les champs manquants selon un ordre fixe. Une absence confirmée et une information indisponible sont distinctes.

La modification expose les métadonnées déjà calculées, sans changer modèle, règles ou corpus. La sortie brute des tokens reste hors de l’interface ; une vue pédagogique expose sur demande la proposition déjà filtrée pour la confidentialité, avant les garde-fous de contenu. Un backend ancien ou non configuré affiche une origine non renseignée plutôt qu’une attribution supposée au modèle.


FastAPI est la couche HTTP Python : elle valide les entrées et sorties avec Pydantic,
appelle le provider et prépare l’audit. Swagger affiche son contrat OpenAPI ; ce n’est
pas le modèle. Le proxy Cloudflare contrôle l’accès à cette API hébergée sur Modal.
vLLM réalise l’inférence du modèle. L’inspecteur permet de relier le formulaire aux
champs JSON et à l’identifiant d’interaction réellement retourné.

Attention à l’interprétation : sur un signal critique reconnu, la politique proposée
remplace systématiquement la proposition. Un statut `safe_fallback` ne suffit donc
pas à conclure que la priorité initiale était fausse. Il faut examiner la proposition
et le motif, puis distinguer conformité technique et pertinence clinique non validée.
