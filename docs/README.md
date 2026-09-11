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

## Suite du SFT — 5 septembre 2026

- [Comparaison et préparation DPO](technical/COMPARAISON_POST_SFT_V1.md)
- [API privée et contrat du fournisseur](technical/API_MODELE_PRIVE_V2.md)
- [Décision proposée post-SFT](decisions/ADR-010-comparaison-et-demonstration-post-sft.md)
- [Preuves locales](evidence/POST_SFT_IMPLEMENTATION_2026-09-05.md)
- [Apprentissage : comparer avant DPO](learning/29-comparer-avant-aligner.md)
- [Apprentissage : API et preuves](learning/30-relier-modele-api-et-preuves.md)

- [Comparaison Kaggle Base/SFT et diagnostic](evidence/BASE_SFT_KAGGLE_2026-09-05.md)

- [Audit de pipeline avant nouvel entraînement](evidence/PIPELINE_AUDIT_2026-09-05.md)
- [Décision de vérification préalable](decisions/ADR-011-verifier-pipeline-avant-entrainement.md)
- [Apprentissage : auditer la pipeline](learning/31-auditer-la-pipeline-avant-entrainer.md)

## Micro-runs du 11 septembre 2026

- [Résultats techniques et limites qualitatives v15–v17](evidence/SFT_MICRO_RUNS_2026-09-11.md)
- [Apprentissage : micro-run et recharge](learning/32-verifier-un-micro-run-et-sa-recharge.md)

## Préparation contrôlée du pilote SFT v2

- [Audit final des données et du trainer](evidence/SFT_V2_READINESS_2026-09-11.md)
- [Comprendre le nettoyage et le pilote](learning/33-donnees-propres-et-pilote-avant-sft.md)
- [Isolation documentaire et budget](decisions/ADR-012-isoler-les-groupes-et-borner-le-pilote-sft.md)
