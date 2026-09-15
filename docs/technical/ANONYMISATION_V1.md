# Anonymisation v1 — politique et implémentation de référence

- **Date :** 2026-08-28
- **Statut :** proposed
- **Implémentation :** `src/triage_poc/anonymization.py`
- **Tests :** `tests/test_anonymization.py`
- **Source :** [documentation Presidio Analyzer](https://microsoft.github.io/presidio/analyzer/), [Presidio Anonymizer](https://microsoft.github.io/presidio/anonymizer/)

## Ce qui est implémenté

Le module `TextAnonymizer` appelle Presidio pour détecter les PII, remplace chaque entité détectée par un jeton non réversible tel que `<EMAIL_ADDRESS>`, puis réanalyse le texte anonymisé. Il produit uniquement le texte transformé et un audit sans texte source ni positions de détection.

La réanalyse ignore uniquement une détection dont la plage est entièrement contenue dans un placeholder généré par cette même passe. Ce traitement évite que le NER français reclasse, par exemple, le contenu de `<PATIENT_REFERENCE>` comme `PERSON`. Une détection résiduelle en dehors d'un placeholder continue de produire `manual_review_required`.

Les langues autorisées sont le français et l'anglais. Le moteur configure `fr_core_news_md` pour le français et `en_core_web_sm` pour l'anglais. Un recognizer de motif complète Presidio pour les références de dossier sous forme synthétique française, par exemple `Patient id: AB-1234`.

## Pourquoi cette politique

- **Remplacement non réversible :** le POC n'a pas besoin de réidentifier une personne ; aucun hash, sel ou mécanisme de déchiffrement n'est donc retenu.
- **Réanalyse :** la détection initiale peut être incomplète ou l'opérateur mal configuré. Une entité encore détectée impose `manual_review_required`.
- **Échec bloquant :** un modèle de langue manquant, une erreur Presidio ou une langue non supportée ne doit jamais faire passer le texte sans contrôle.
- **Audit minimal :** seuls langue, comptes par type d'entité et statut sont conservés. L'audit ne contient jamais le texte original, les valeurs détectées ou leurs positions.

## Comment l'utiliser

```python
from triage_poc.anonymization import TextAnonymizer

result = TextAnonymizer().anonymize(
    "Texte synthétique à contrôler.",
    language="fr",
)

if result.audit.status != "passed":
    raise RuntimeError("Manual review required before ingestion")
```

## Limites et conditions d'utilisation

Presidio est une couche de détection, non une garantie d'anonymisation exhaustive ou de conformité juridique. Une entité non détectée peut rester présente ; les contrôles automatiques doivent donc être complétés par une revue humaine d'échantillons avant ingestion. Le module ne traite pas encore des fichiers structurés, de documents PDF, d'images ou de pseudonymisation avec cohérence inter-enregistrements.

Les tests automatisés utilisent des chaînes synthétiques et des doubles de test. La validation d'intégration réelle avec `fr_core_news_md 3.8.0` et `en_core_web_sm 3.8.0` est consignée dans l'[audit de reprise du corpus](../evidence/AUDIT_CORPUS_ETAPE_1_2026-09-16.md). Elle vérifie des noms, une référence patient et des emails synthétiques ; elle ne mesure pas le rappel sur toutes les formes de PII.
