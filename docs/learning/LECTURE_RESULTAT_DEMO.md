# Lire le résultat de la démonstration

Date : 2026-10-08 · Statut : draft
Sources : api.py, demo_ui/app.js, guardrails.py et collection.py.

Le frontend affiche le résultat final après contrôles. Le statut conservé, corrigé ou remplacé explique l’intervention des garde-fous. Il ne prouve pas la qualité clinique. Les questions de collecte suivent les champs manquants selon un ordre fixe. Une absence confirmée et une information indisponible sont distinctes.

La modification expose les métadonnées déjà calculées, sans changer modèle, règles ou corpus. Le texte brut avant contrôle reste hors de l’interface. Un backend ancien ou non configuré affiche une origine non renseignée plutôt qu’une attribution supposée au modèle.
