# Documentation du projet

Ce dossier sépare volontairement les notes d'apprentissage des documents techniques et des preuves professionnelles. Les règles détaillées sont dans [`AGENTS.md`](../AGENTS.md).

La roadmap active et son état de preuve sont dans [`technical/ROADMAP_POC_V1.md`](technical/ROADMAP_POC_V1.md).

| Emplacement | Contenu attendu | Ne pas y mettre |
|---|---|---|
| `learning/` | Notes pédagogiques, exercices, glossaire, questions ouvertes | Affirmations de performance ou de validation clinique |
| `technical/` | Architecture, contrats d'API, guides de reproduction, data cards | Notes de cours non vérifiées |
| `decisions/` | ADR et décisions traçables | Décisions implicites dans un journal libre |
| `evidence/` | Protocoles, résultats, environnement et limites de preuve | Données patient, logs bruts ou secrets |
| `governance/` | Licences, provenance, anonymisation, risques | Jeux de données bruts |

Le rapport final public est dans `../reports/`. Les données lourdes ou sensibles ne sont pas versionnées : seuls les manifestes, schémas, échantillons synthétiques et checksums peuvent l'être.
