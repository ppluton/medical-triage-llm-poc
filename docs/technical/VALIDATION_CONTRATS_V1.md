# Validation des contrats de données v1

- **Date :** 2026-08-28
- **Statut :** implemented
- **Code :** `src/triage_poc/contracts.py`

Le projet valide désormais les objets en mémoire contre les JSON Schemas versionnés dans `data/manifests/`. Cette validation s'applique aux manifestes de source et aux enregistrements SFT/DPO/évaluation avant qu'un objet ne soit admis dans une étape suivante.

Le fixture `data/samples/synthetic-triage-record-v1.json` est exclusivement synthétique. Il montre la structure d'un scénario d'évaluation ; son statut clinique est `pending` et il ne prouve aucune décision de triage.

La validation arrête le flux en cas d'erreur et ne journalise pas le contenu de l'enregistrement. Elle ne remplace ni les contrôles PII, ni l'inspection de licence, ni la revue clinique : elle vérifie uniquement que leurs statuts et métadonnées sont présents et cohérents avec le contrat.
