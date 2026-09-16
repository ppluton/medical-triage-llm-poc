# Audit de reprise du corpus — étape 1

Date : 2026-09-16 — Statut : partially_proven

Périmètre : sources locales épinglées, candidat SFT v2.1, lot DPO revu techniquement, schéma de métadonnées et contrôle d’anonymisation. Aucun entraînement, aucune validation clinique et aucune publication externe.

Environnement : macOS, worktree `codex/complete-poc-evaluation`, HEAD de départ `a213f51728ecf861b77b256f4e7ac9316c591aea`, Python 3.13 du projet, Presidio Analyzer/Anonymizer 2.2.364, spaCy 3.8.16, `fr_core_news_md 3.8.0`, `en_core_web_sm 3.8.0`, Transformers 4.57.6.

## Claim vérifié

Le dépôt contient-il un corpus bilingue proche de 5 000 paires, traçable et techniquement prêt pour la préparation SFT, un lot DPO traçable, un schéma de métadonnées et une justification honnête des contrôles RGPD ?

## Sources et intégrité

| Source | Preuve locale | Résultat |
|---|---|---|
| MediQAl | HEAD du checkout | `5af34948a74c7b8807c476204a21149ffb00ea2c`, checkout sans changement suivi |
| FrenchMedMCQA | SHA-256 et taille de l’archive | `58724ce1…af4c9`, 550 466 octets, conforme au manifeste |
| MedQuAD | HEAD, `git archive` | `577bd37b…e96cb`, archive `9dd2db77…c64a8`, 45 649 920 octets, conforme |
| UltraMedical-Preference | concaténation opaque train/dev/test | `d40f19d8…926c`, 1 019 500 856 octets, conforme |

Les pages amont ont été relues le 16 septembre : MediQAl affiche CC BY 4.0, FrenchMedMCQA Apache-2.0, MedQuAD CC BY 4.0 et UltraMedical-Preference MIT. Il s’agit des licences affichées, pas d’un avis juridique.

## Candidat SFT observé

| Contrôle | Résultat |
|---|---|
| Canonique | 4 700 lignes ; hash `687617f5…6567d` conforme |
| Train | 3 721 conversations ; hash `70270d65…f4f9b` conforme |
| Validation | 479 conversations ; hash `554ee8ad…c74f25` conforme |
| Test | 500 lignes dans le canonique, non rendu pour l’entraînement |
| Langues | 2 474 FR, 2 226 EN |
| Sources | MediQAl 1 475, FrenchMedMCQA 999, MedQuAD 2 226 |
| Identité | 4 700 `record_id` uniques et 4 700 locators source uniques |
| Fidélité déclarée | zéro troncature, zéro label de triage, 4 700 statuts cliniques `not_performed` |

Le rejeu complet source/tokenizer `val_894387e20361` s'est terminé avec le code 0 en 620 secondes :

- 4 200 enregistrements de développement contrôlés ;
- 4 195 correspondances source exactes et cinq transformations reproduites par le rejeu de l'anonymisation ;
- 2 224 QCM contrôlés avec leurs options ;
- 8 400 champs rescannés, sans alerte résiduelle pour la politique d'identifiants directs ;
- 3 721 frontières de prompt train et 479 validation exactes, un EOS natif par ligne, zéro dépassement de 2 048 tokens ;
- zéro groupe de contenu défini traversant les splits, zéro exclusion supplémentaire ;
- zéro génération ou revue de réponse du test et zéro étape d'entraînement.

Le statut produit est `technical_audit_passed`. Le rapport rappelle que le groupement n'exclut pas toute paraphrase sémantique et que l'accord avec la source ne prouve ni exactitude médicale ni absence de toute PII.

## Intégration Presidio réelle et correction ciblée

Un test synthétique avec les moteurs réels a détecté puis remplacé :

- en français : un nom, une référence patient et un email ;
- en anglais : un nom et un email.

La première exécution française a signalé un faux résidu : le NER reclassait le contenu du placeholder généré `<PATIENT_REFERENCE>` comme `PERSON`. `TextAnonymizer` filtre désormais uniquement les détections entièrement contenues dans ses propres placeholders. Après correction, les deux cas ont le statut `passed` et zéro résidu. Le test unitaire opposé prouve qu'une détection hors placeholder reste `manual_review_required`.

Commande d'intégration :

```bash
PYTHONPATH=src /Users/ppluton/Documents/ChatGPT/Medical_train_llm/.venv/bin/python - <<'PY'
from triage_poc.anonymization import TextAnonymizer

cases = {
    "fr": "Mme Jeanne Martin, dossier numéro AB-1234, email jeanne.martin@example.com.",
    "en": "Patient John Smith can be reached at john.smith@example.com.",
}
anonymizer = TextAnonymizer()
for language, text in cases.items():
    result = anonymizer.anonymize(text, language)
    print(language, result.audit.detected_entity_counts,
          result.audit.residual_entity_counts, result.audit.status)
    print(result.text)
PY
```

Cette preuve porte sur ces cas contrôlés ; elle ne transforme pas Presidio en garantie de rappel exhaustif.

## Lot DPO observé

| Contrôle | Train | Validation |
|---|---:|---:|
| Lignes | 426 | 54 |
| SHA-256 | `5a3bb76a…f6674` | `2052ae0a…1c53e8` |
| Langue | 426 EN | 54 EN |
| Statut clinique `not_performed` | 426 | 54 |

Les 480 identifiants et locators sont uniques. Le lot historique v1 avait des statuts projet/confidentialité `approved_for_educational_dpo`, mais ses 480 justifications portaient encore la mention contradictoire `project review pending` et son manifeste ne renseignait pas explicitement le manifeste SFT courant.

La [consolidation v2](DPO_PROJECT_REVIEW_V2_2026-09-16.md) corrige ces deux défauts sans modifier `prompt`, `chosen`, `rejected`, les splits, le type de label ni la provenance. Le lot v2 contient 426/54 lignes, zéro justification en attente, 480 liens vers `ADR-014` et une protection explicitement reliée aux 4 700 lignes SFT. `clinical_review_status: not_performed` reste inchangé et indique correctement qu'aucun professionnel de santé réel n'a participé au scénario scolaire.

## Schéma de métadonnées

Le schéma `clinical_metadata_v1.schema.json` rend obligatoires symptômes, antécédents, constantes, source immuable, confiance et statuts de qualité. Sa branche `not_available` interdit de remplir silencieusement les champs absents. Deux fixtures synthétiques couvrent les cas renseigné et indisponible.

Validation ciblée exécutée après ajout :

```bash
PYTHONPATH=src /Users/ppluton/Documents/ChatGPT/Medical_train_llm/.venv/bin/python \
  -m pytest tests/test_anonymization.py tests/test_clinical_metadata_schema.py \
  tests/test_source_sft.py -q
```

Résultat ciblé final : **22 tests réussis**. Ruff réussit sur les fichiers Python modifiés.

La suite complète finale `val_50912d5d4674` termine avec le code 0 : **176 tests réussis en 8,13 s**, avec une dépréciation Starlette/httpx déjà connue. Cette preuve couvre les régressions locales ; elle n'ajoute aucune validation clinique.

## Verdict par exigence

| Exigence | Niveau | Limite |
|---|---|---|
| Inventaire/version/licence | prouvé localement | aucune validation juridique |
| SFT bilingue ≈5 000 | prouvé pour 4 700 lignes | QA médicale sans labels de triage ni revue clinique |
| Train/validation/test séparés | prouvé selon les groupes définis | pas de garantie contre toute paraphrase sémantique |
| Métadonnées définies | schéma et fixtures prouvés par tests | non rétro-remplies dans v2.1 |
| Anonymisation | partiellement prouvé | identifiants directs contrôlés ; contexte et conformité RGPD non certifiés |
| DPO | intégrité, lignée et revue éducative prouvées | 480 EN ; aucune validation professionnelle ni preuve d'alignement FR |
| Évaluation de POC séparée | jeux synthétiques séparés présents | références proposées et test déjà consulté ; aucune étude clinique revendiquée |

Cette preuve historique constatait une porte PII ouverte sur v2.1. La
[finalisation v2.2](SFT_PRIVACY_FINALIZATION_2026-09-16.md) masque ensuite les alertes
directes, rescane le corpus et fige le manifeste admis pour l'entraînement pédagogique
contrôlé. La publication externe et la certification RGPD restent bloquées. La consolidation
DPO est terminée. Une validation indépendante par des professionnels appartient à la
roadmap d'un pilote réel ; son absence ne bloque pas le POC OpenClassrooms.
