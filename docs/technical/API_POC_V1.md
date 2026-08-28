# API POC v1

- **Statut :** implemented contract only
- **Route :** `POST /v1/triage`

La route valide les entrées et retourne la structure spécifiée, y compris l'avertissement de sécurité. Sans fournisseur de modèle configuré, elle répond `503` : aucune règle clinique n'est simulée. Les tests utilisent un fournisseur synthétique.
