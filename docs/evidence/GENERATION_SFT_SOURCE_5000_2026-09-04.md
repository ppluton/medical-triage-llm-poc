# Preuve de génération du SFT médical source-derived 5 000

- **Date :** 2026-09-04
- **Statut :** proven for local educational SFT; share with caveats
- **Run retenu :** `source-sft-v1-2026-09-04-final`
- **Révision du générateur :** `f0431d3`
- **Environnement :** macOS, Python 3.13, Presidio, spaCy FR/EN
- **Sources :** manifestes épinglés MedQuAD, MediQAl et FrenchMedMCQA ; ADR-008

## Question vérifiée

Le pipeline produit-il exactement 5 000 paires médicales bilingues issues des sources, avec provenance, contrôles d'identifiants directs et splits isolés, sans inventer de réponse ou de label de triage ?

## Résultat observé

| Contrôle | Résultat |
|---|---:|
| Enregistrements canoniques | 5 000 |
| Anglais / français | 2 500 / 2 500 |
| Train / validation / test | 4 000 / 500 / 500 |
| MedQuAD / MediQAl / FrenchMedMCQA | 2 500 / 1 500 / 1 000 |
| Réponses `source_provided` | 5 000 |
| Labels de triage ajoutés | 0 |
| Identifiants de ligne uniques | 5 000 |
| Questions normalisées uniques | 5 000 |
| Locators source dupliqués | 0 |
| Instructions ou réponses vides | 0 |
| Réponses tronquées | 101 (2,02 %) |
| Identifiants directs détectés et masqués | 1 email, 12 téléphones |
| Placeholders contextuels `PERSON/LOCATION/DATE_TIME` | 0 |

Répartition par split et source :

| Source | Train | Validation | Test |
|---|---:|---:|---:|
| MedQuAD | 2 000 | 250 | 250 |
| MediQAl | 1 200 | 150 | 150 |
| FrenchMedMCQA | 800 | 100 | 100 |

## Artefacts locaux hors Git

| Artefact | Lignes | SHA-256 |
|---|---:|---|
| `source-sft-v1.jsonl` | 5 000 | `da7b7913cc70a4cd1c340d8afb1bfcc910af5eb7b8511f81b18f356d8420b347` |
| `train-qwen3.jsonl` | 4 000 | `854ce4f0458d1d313e77d7e3ff9da2d2dffb6571af728a7237f8aada7ce5525d` |
| `validation-qwen3.jsonl` | 500 | `7118258c5fdbfe47d5c11b5c4e4b2c2600c4ed17a1eb4b806b0bf5f7c2c52296` |

Les empreintes ont été recalculées avec `shasum -a 256` et correspondent au manifeste `data/manifests/derived-source-medical-qa-sft-v1.json`.

## Échec intermédiaire conservé

La passe `source-sft-v1-2026-09-04` avait les bons volumes, mais l'audit d'un échantillon déterministe a montré que le NER Presidio générique remplaçait des termes médicaux par `<PERSON>` ou `<LOCATION>`. Cette version a été classée **needs revision** et n'est pas retenue.

La politique finale limite Presidio aux identifiants directs. Ce changement a supprimé les placeholders contextuels dommageables tout en conservant la détection de téléphone, email, carte, IBAN, IP et référence patient.

## Commande reproductible

La commande complète et les entrées attendues sont documentées dans `docs/technical/DATASET_SFT_SOURCE_5000_V1.md`. Le script exécute aussi la validation JSON Schema et refuse les doublons après anonymisation.

## Ce que cette preuve établit

- le volume, les quotas, l'origine et les splits annoncés sont observés ;
- les fichiers train et validation sont rendus au format Qwen3 ;
- le test n'est pas rendu dans un fichier d'entraînement ;
- aucune cible de triage n'a été fabriquée à partir des corpus QA.

## Ce qu'elle n'établit pas

- la correction médicale de chaque réponse source ;
- une anonymisation exhaustive ou une conformité RGPD certifiée ;
- l'absence de doublons sémantiques ;
- une compétence de triage du modèle ;
- un gain après fine-tuning, car aucun run complet n'est encore mesuré.

## Évaluation de confiance

**Share with caveats.** Le dataset est suffisamment contrôlé pour un entraînement scolaire local. Les 101 troncatures et l'absence de revue clinique doivent rester visibles dans le rapport et lors de la soutenance.
