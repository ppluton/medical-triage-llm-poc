# Spécification fonctionnelle et technique — POC Agent IA de triage médical

## 1. Finalité

Exposer une API de démonstration qui reçoit un contexte symptomatique, guide une collecte complémentaire, puis retourne une priorité de triage, une explication encadrée et une trace d’audit. Le POC assiste le triage initial au CHSA ; il ne remplace jamais l’évaluation clinique.

## 2. Parcours cible

```text
Patient ou opérateur
  → questionnaire adaptatif
  → validation et normalisation des informations
  → Qwen3-1.7B-Base + adaptateurs SFT/LoRA/DPO
  → contrôles de sécurité et d’escalade
  → priorité, explication et logs d’audit
```

## 3. Exigences fonctionnelles

### Entrées

L’agent collecte, lorsqu’elles sont disponibles :

- symptôme principal, durée, évolution et intensité ;
- symptômes associés et signaux d’alerte ;
- antécédents, allergies et traitements pertinents ;
- constantes vitales ;
- facteurs de vulnérabilité.

Les questions complémentaires doivent être adaptées aux réponses précédentes.

### Sorties

Le système retourne :

- `maximum`, `moderate` ou `deferred` comme niveau de priorité ;
- une synthèse des éléments considérés ;
- les informations manquantes pertinentes ;
- les éventuels signaux d’alerte ;
- une recommandation encadrée ;
- un avertissement indiquant que l’évaluation ne remplace pas un professionnel de santé.

## 4. Données et gouvernance

### Sources prévues

- [MediQAl (`ANR-MALADES/MediQAl`)](https://huggingface.co/datasets/ANR-MALADES/MediQAl) ;
- [FrenchMedMCQA (`qanastek/frenchmedmcqa`)](https://huggingface.co/datasets/qanastek/frenchmedmcqa) ;
- [MedQuAD (`abachaa/MedQuAD`)](https://github.com/abachaa/MedQuAD) ;
- [UltraMedical-Preference](https://huggingface.co/datasets/TsinghuaC3I/UltraMedical-Preference).

Documenter, pour chaque source, l’URL, la version, la licence, les restrictions d’usage, les transformations et la provenance de chaque enregistrement.

### Dataset SFT

Cible : environ 5 000 paires instruction-réponse en français et en anglais. Le dataset est séparé en `train`, `validation` et `test` ; le jeu d’évaluation clinique est isolé de tout entraînement.

### Dataset DPO

Chaque exemple associe un même contexte à une réponse `chosen` et une réponse `rejected`. Les préférences doivent être justifiées et validées cliniquement.

### Schéma minimal

```json
{
  "id": "sft-000001",
  "language": "fr",
  "instruction": "Patient présentant une douleur thoracique depuis 30 minutes.",
  "response": "Niveau de priorité : urgence maximale. Une évaluation immédiate est nécessaire.",
  "symptoms": ["douleur thoracique"],
  "medical_history": [],
  "vitals": {"heart_rate": null, "temperature_c": null},
  "triage_level": "maximum",
  "source_dataset": "source-name",
  "source_license": "to-document",
  "clinical_review_status": "approved",
  "pii_anonymization_status": "passed",
  "split": "train",
  "transformation_version": "git-sha"
}
```

### Anonymisation

Utiliser Presidio :

1. `AnalyzerEngine` pour détecter les données personnelles ;
2. `AnonymizerEngine` pour appliquer `replace`, `mask` ou `redact` ;
3. un modèle linguistique adapté, notamment `fr_core_news_md` pour le français ;
4. des contrôles automatiques et une revue manuelle d’échantillons ;
5. un journal des transformations.

## 5. Entraînement et alignement

### SFT + LoRA

- Base : `Qwen3-1.7B-Base`.
- Démarrer par des runs LoRA courts pour valider la pipeline.
- Versionner les hyperparamètres, la seed, les données et les checkpoints.
- Sauvegarder loss, métriques de validation et artefacts de reprise.
- Surveiller le sur-apprentissage.

### DPO

- Partir du checkpoint SFT validé.
- Entraîner sur les paires de préférences d’UltraMedical-Preference et les paires validées du projet.
- Mesurer le gain par rapport au modèle de base et au modèle SFT.
- Tester spécifiquement hallucinations, réponses banalisantes et recommandations dangereuses.

## 6. Évaluation

Les seuils d’acceptation doivent être définis avec les référents cliniques. Les mesures à produire comprennent :

- cohérence de la priorité proposée ;
- rappel des cas critiques ;
- sous-triage et sur-triage ;
- réponses dangereuses ou non conformes ;
- qualité des explications et des questions complémentaires ;
- latence p50/p95, taux d’erreur et débit ;
- couverture et exploitabilité des logs d’audit.

Le jeu de tests comprend des scénarios synthétiques de douleur thoracique, détresse respiratoire, déficit neurologique, symptômes pédiatriques, grossesse, vulnérabilité, contexte insuffisant ou contradictoire, et requêtes FR/EN.

## 7. Architecture technique

| Composant | Technologie | Rôle |
|---|---|---|
| API | FastAPI | Validation, orchestration, réponse structurée |
| Modèle | Qwen3-1.7B-Base | Génération spécialisée |
| Adaptation | Transformers, PEFT, LoRA, DPO | SFT et alignement |
| Inférence | vLLM | Service performant du modèle |
| Conteneur | Docker | Packaging et reproductibilité |
| Datasets | Hugging Face Datasets | Chargement, transformations et versionnage |
| Anonymisation | Presidio | Détection et masquage de PII |
| Tracking | MLflow ou Weights & Biases | Métriques, logs et checkpoints |
| CI/CD | GitHub Actions | Tests, build, déploiement pilote |

## 8. API

### `POST /v1/triage`

Entrée :

```json
{
  "language": "fr",
  "patient_context": {
    "age_group": "adult",
    "symptoms": ["douleur thoracique", "essoufflement"],
    "duration": "30 minutes",
    "medical_history": [],
    "vitals": {"temperature_c": null, "heart_rate": null}
  }
}
```

Sortie :

```json
{
  "interaction_id": "uuid",
  "triage_level": "maximum",
  "summary": "Les symptômes déclarés nécessitent une évaluation immédiate.",
  "clinical_rationale": ["Douleur thoracique aiguë", "Essoufflement associé"],
  "missing_information": ["Constantes vitales"],
  "safety_notice": "Cette évaluation est une aide au triage et ne remplace pas un professionnel de santé.",
  "model_version": "qwen3-1.7b-dpo-v1",
  "latency_ms": 850
}
```

## 9. Traçabilité, sécurité et exploitation

Chaque interaction journalise : identifiant, horodatage, versions du modèle/prompt/garde-fous, entrée anonymisée, sortie, statut des contrôles et latence.

Exigences :

- ne jamais commiter de clés ou secrets ;
- restreindre l’accès à l’endpoint pilote ;
- minimiser les données journalisées ;
- surveiller erreurs et latence après déploiement ;
- documenter les limites d’usage ;
- produire une checklist `go / no-go` pour toute évolution au-delà du POC.

## 10. CI/CD

GitHub Actions automatise :

1. lint et tests unitaires ;
2. validation des schémas de données ;
3. contrôles d’anonymisation ;
4. tests de non-régression et de sécurité ;
5. build Docker ;
6. tests d’intégration FastAPI ;
7. déploiement pilote ;
8. smoke test et collecte des métriques.

## 11. Conditions de livraison

Le POC est présentable lorsque le dataset est documenté et anonymisé, que le modèle est reproductible, que les résultats SFT/DPO sont comparés, que les limites sont explicites, que l’endpoint pilote est accessible et que le rapport final contient les métriques et la roadmap de déploiement.
