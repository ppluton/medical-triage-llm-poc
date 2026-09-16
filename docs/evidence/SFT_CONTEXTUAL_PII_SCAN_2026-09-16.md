# Scan PII contextuel du corpus SFT v2.1

- Date : 2026-09-16
- Statut : scan terminé, revue directe et contextuelle en attente
- Résultat compact : [JSON compagnon](SFT_CONTEXTUAL_PII_SCAN_2026-09-16.json)
- Entrée : 4 700 lignes du canonique `source-sft-v2.1.jsonl`
- Statut juridique : aucune certification RGPD délivrée
- Statut clinique : aucune validation clinique.

## Question

Le corpus SFT candidat a-t-il été parcouru intégralement avec une détection PII bilingue,
et quelles décisions restent nécessaires avant de le déclarer prêt à diffuser ?

## Exécution

Le job `val_0fd624a7c572` a analysé les champs `instruction` et `response` des 4 700
lignes, soit 9 400 champs, avec Presidio Analyzer 2.2.364 et les modèles spaCy FR/EN.
Il s'est terminé avec le code 0 en 315 secondes.

```sh
PYTHONPATH=src python scripts/audit_sft_contextual_pii.py \
  --canonical data/processed/source-sft-v2.1-reviewed/source-sft-v2.1.jsonl \
  --output artifacts/sft-context-review-v2

PYTHONPATH=src python scripts/prepare_sft_direct_pii_review.py \
  --findings artifacts/sft-context-review-v2/findings-private.jsonl \
  --output artifacts/sft-context-review-v2/direct-review-private.jsonl
```

Le répertoire et ses fichiers sont privés (`0700` et `0600`) et ignorés par Git. Le
rapport versionné conserve uniquement des nombres, statuts et empreintes. La régression
complète `val_7c2aff4810d7` passe 197 tests en 15,13 secondes, avec un avertissement externe
Starlette/httpx déjà connu. Ruff passe sur les composants PII.

## Résultats observés

| État par ligne | Nombre |
|---|---:|
| Aucun candidat contextuel détecté | 1 498 |
| Revue contextuelle requise | 3 180 |
| Revue prioritaire `PATIENT_NAME` requise | 22 |
| Total | 4 700 |

Les détections sont `PERSON` 5 433, `LOCATION` 3 491, `DATE_TIME` 844 et
`PATIENT_NAME` 31. Les 31 détections de nom explicite concernent 22 lignes et ont été
extraites dans une file privée de revue. Aucune décision humaine n'a encore été inscrite.

Ces nombres ne signifient pas que 3 202 lignes contiennent des patients identifiables.
Les corpus médicaux citent des auteurs, organismes, lieux, éponymes et durées que le NER
peut classer comme personnes, lieux ou dates. Inversement, l'absence de détection n'est pas
une garantie de rappel exhaustif.

## Ce que cela prouve

Le canonique désigné par l'empreinte du manifeste a été parcouru intégralement ; chaque
ligne possède une décision text-free reliée à son identifiant, sa source et son split. Les
candidats directs disposent maintenant d'une file de revue actionnable sans exposer leur
texte dans Git. Les 500 lignes de test ont été scannées uniquement pour la confidentialité,
sans utiliser leur contenu pour choisir un modèle.

## Ce que cela ne prouve pas

Le corpus n'est pas encore autorisé à la diffusion et ne doit pas être présenté comme
« certifié anonyme ». Il reste à examiner les 22 lignes prioritaires, décider conserver,
masquer ou exclure, puis traiter les détections contextuelles selon une procédure de revue
documentée. Toute transformation produira une nouvelle version du canonique et de nouvelles
empreintes ; elle ne doit pas modifier silencieusement le jeu existant.
