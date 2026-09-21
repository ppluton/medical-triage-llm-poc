# Index des preuves

- Date : 2026-09-21
- Statut : `draft`
- Sources : [rapport technique](../../reports/RAPPORT_TECHNIQUE_POC.md) (section 12), fichiers de ce dossier

Cet index classe les preuves versionnées. Une preuve décrit une mesure observée dans un environnement donné ; elle ne constitue pas une validation clinique. Les priorités et garde-fous cités restent `proposed`.

## Preuves finales citées par le rapport

- [PIPELINE_AUDIT_2026-09-05.md](PIPELINE_AUDIT_2026-09-05.md) — Audit du pipeline de données avant le nouvel entraînement (défauts détectés et corrections).
- [SFT_PRIVACY_FINALIZATION_2026-09-16.md](SFT_PRIVACY_FINALIZATION_2026-09-16.md) — Finalisation technique de la confidentialité du corpus SFT v2.2 (masquage et rescan, sans certification RGPD).
- [DPO_V22_LINEAGE_REBIND_2026-09-16.md](DPO_V22_LINEAGE_REBIND_2026-09-16.md) — Réancrage des 480 paires DPO sur le corpus SFT v2.2, sans modification des préférences.
- [SFT_V39_RESULT_2026-09-16.md](SFT_V39_RESULT_2026-09-16.md) — Résultat du SFT final v2.2 sur Kaggle v39 (150 étapes, métriques appariées).
- [SFT_V40_RELOAD_RESULT_2026-09-16.md](SFT_V40_RELOAD_RESULT_2026-09-16.md) — Recharge en lecture seule du checkpoint SFT v39 sur Kaggle v40.
- [DPO_V41_RESULT_2026-09-16.md](DPO_V41_RESULT_2026-09-16.md) — DPO borné v41 (20 étapes) à partir du SFT v39 : intégrité des poids et métriques internes.
- [COMPARISON_V43_RESULT_2026-09-16.md](COMPARISON_V43_RESULT_2026-09-16.md) — Comparaison Base / SFT v39 / DPO v41 sur le développement et sélection conservatrice du SFT.
- [SELECTED_RESERVE_V46_RESULT_2026-09-16.md](SELECTED_RESERVE_V46_RESULT_2026-09-16.md) — Réserve finale ouverte une seule fois sur le SFT retenu : résultat négatif figé (0/18 JSON conforme).
- [VLLM_V37_RESULT_2026-09-16.md](VLLM_V37_RESULT_2026-09-16.md) — Système vLLM + API 0.4.0 avec garde-fous : exécution Base/SFT/DPO et dialogues FR/EN.
- [STAGE2_SAFETY_V37_BLIND_REVIEW_2026-09-16.md](STAGE2_SAFETY_V37_BLIND_REVIEW_2026-09-16.md) — Revue qualitative aveugle des sorties v37.
- [MODAL_DEPLOYMENT_2026-09-16.md](MODAL_DEPLOYMENT_2026-09-16.md) — Déploiement pilote Modal (GPU T4, scale-to-zero) et smoke tests rapprochés de l'audit.
- [CLOUDFLARE_PAGES_DEPLOYMENT_2026-09-16.md](CLOUDFLARE_PAGES_DEPLOYMENT_2026-09-16.md) — Frontend Cloudflare Pages public, proxy authentifié vers Modal, deux scénarios synthétiques bout en bout.

## Preuves intermédiaires

Étapes antérieures, essais, échecs et données de mesure associées, classés par étape. Elles expliquent le chemin suivi et ne décrivent pas l'état final.

### Données et corpus

- [Acquisition et audit candidat MEDIQA 2019](ACQUISITION_AUDIT_MEDIQA_2026-08-31.md)
- [Acquisition et audit candidat MedQuAD](ACQUISITION_AUDIT_MEDQUAD_2026-08-31.md)
- [Acquisition et audit candidat UltraMedical-Preference](ACQUISITION_AUDIT_ULTRAMEDICAL_PREFERENCE_2026-08-31.md)
- [Acquisition contrôlée — FrenchMedMCQA](ACQUISITION_FRENCHMEDMCQA_2026-08-28.md)
- [Preuve locale — anonymisation v1](ANONYMISATION_V1_LOCAL.md)
- [Audit de reprise du corpus — étape 1](AUDIT_CORPUS_ETAPE_1_2026-09-16.md)
- [Génération de la file SFT candidate v2 avec MediQAl](GENERATION_FILE_SFT_5000_V2_2026-09-03.md)
- [Preuve de génération SFT expérimentale 5 000](GENERATION_SFT_EXPERIMENTAL_5000_2026-09-03.md)
- [Preuve de génération du SFT médical source-derived 5 000](GENERATION_SFT_SOURCE_5000_2026-09-04.md)
- [Ressource Kaggle privée Qwen3-1.7B-Base](QWEN3_BASE_KAGGLE_RESOURCE_2026-09-16.md)
- [Preuve — reconstruction des splits FrenchMedMCQA](RECONSTRUCTION_FRENCHMEDMCQA_2026-08-28.md)
- [Reconstruction des splits UltraMedical-Preference](RECONSTRUCTION_ULTRAMEDICAL_SPLITS_2026-08-31.md)
- [Scan PII contextuel du corpus SFT v2.1](SFT_CONTEXTUAL_PII_SCAN_2026-09-16.md)

Données de mesure associées : [PIPELINE_AUDIT_V1.json](PIPELINE_AUDIT_V1.json), [PIPELINE_AUDIT_V2.json](PIPELINE_AUDIT_V2.json), [SFT_CONTEXTUAL_PII_SCAN_2026-09-16.json](SFT_CONTEXTUAL_PII_SCAN_2026-09-16.json), [SFT_LABEL_AUDIT_V14.json](SFT_LABEL_AUDIT_V14.json), [SFT_MEDQUAD_STYLE_DIAGNOSTIC_2026-09-11.json](SFT_MEDQUAD_STYLE_DIAGNOSTIC_2026-09-11.json), [SFT_V2_GROUP_AUDIT_2026-09-11.json](SFT_V2_GROUP_AUDIT_2026-09-11.json), [SFT_V2_SOURCE_PROVENANCE_RECHECK.json](SFT_V2_SOURCE_PROVENANCE_RECHECK.json), [SFT_V2_SOURCE_REVIEW_EXCLUSIONS.json](SFT_V2_SOURCE_REVIEW_EXCLUSIONS.json).

### Baseline et SFT

- [Baseline synthétique Qwen3 Base](BASELINE_QWEN3_BASE_2026-08-31.md)
- [Comparaison Base/SFT sur Kaggle — validation v8](BASE_SFT_KAGGLE_2026-09-05.md)
- [Validation locale de la chaîne post-SFT](POST_SFT_IMPLEMENTATION_2026-09-05.md)
- [Correction du passage évaluation → entraînement en précision mixte](SFT_FP16_FIX_2026-09-11.md)
- [Résultat final du SFT complet sur Kaggle — version 5](SFT_KAGGLE_FULL_RUN_2026-09-04.md)
- [Diagnostic v21 — douze réponses apprises, généralisation non mesurée](SFT_MEMORIZATION_V21_RESULT_2026-09-11.md)
- [Micro-runs correctifs SFT — 11 septembre 2026](SFT_MICRO_RUNS_2026-09-11.md)
- [Micro-run SFT source-derived avec Unsloth Core/MLX](SFT_SOURCE_MICRO_RUN_2026-09-04.md)
- [Pilote SFT v19 — mécanique validée, progrès partiels et limites qualitatives](SFT_V19_PILOT_RESULT_2026-09-11.md)
- [Vérification v20 — recharge exacte, checkpoints comparés, qualité non acquise](SFT_V20_CHECKPOINT_RESULT_2026-09-11.md)
- [Évaluation v22 — reprise réussie, forme améliorée, exactitude non acquise](SFT_V22_RESULT_2026-09-12.md)
- [Pilote SFT v18 — baseline sauvegardée, optimisation interrompue](SFT_V2_PILOT_V18_2026-09-11.md)
- [Vérification avant le pilote SFT v2 — 11 septembre 2026](SFT_V2_READINESS_2026-09-11.md)
- [Vérification locale Unsloth — chargement d'inférence](UNSLOTH_LOCAL_INFERENCE_2026-08-30.md)
- [Micro-run SFT synthétique avec Unsloth Core/MLX](UNSLOTH_TRAIN_PREPARATION_2026-08-30.md)

Données de mesure associées : [BASE_SFT_KAGGLE_V10_SUMMARY.json](BASE_SFT_KAGGLE_V10_SUMMARY.json), [BASE_SFT_KAGGLE_V11_FP16_SUMMARY.json](BASE_SFT_KAGGLE_V11_FP16_SUMMARY.json), [BASE_SFT_KAGGLE_V11_NF4_SUMMARY.json](BASE_SFT_KAGGLE_V11_NF4_SUMMARY.json), [BASE_SFT_KAGGLE_V13_SUMMARY.json](BASE_SFT_KAGGLE_V13_SUMMARY.json), [BASE_SFT_KAGGLE_V8_REVIEW.json](BASE_SFT_KAGGLE_V8_REVIEW.json), [BASE_SFT_KAGGLE_V8_SUMMARY.json](BASE_SFT_KAGGLE_V8_SUMMARY.json), [SFT_CONTINUATION_V22_LAUNCH_2026-09-11.json](SFT_CONTINUATION_V22_LAUNCH_2026-09-11.json), [SFT_FP16_CPU_CONTRACT_2026-09-11.json](SFT_FP16_CPU_CONTRACT_2026-09-11.json), [SFT_MEMORIZATION_V21_ARCHIVE_2026-09-11.json](SFT_MEMORIZATION_V21_ARCHIVE_2026-09-11.json), [SFT_MEMORIZATION_V21_LAUNCH_2026-09-11.json](SFT_MEMORIZATION_V21_LAUNCH_2026-09-11.json), [SFT_MEMORIZATION_V21_RESULT_2026-09-11.json](SFT_MEMORIZATION_V21_RESULT_2026-09-11.json), [SFT_PILOT_REFERENCE_LENGTHS_2026-09-11.json](SFT_PILOT_REFERENCE_LENGTHS_2026-09-11.json), [SFT_PRIVACY_FINALIZATION_2026-09-16.json](SFT_PRIVACY_FINALIZATION_2026-09-16.json), [SFT_SUPERVISED_TOKEN_VOLUME_2026-09-11.json](SFT_SUPERVISED_TOKEN_VOLUME_2026-09-11.json), [SFT_TRAINER_CONTRACT_CPU_2026-09-11.json](SFT_TRAINER_CONTRACT_CPU_2026-09-11.json), [SFT_V19_CHECKPOINT_ARCHIVE_2026-09-11.json](SFT_V19_CHECKPOINT_ARCHIVE_2026-09-11.json), [SFT_V19_OUTPUT_REVIEW_2026-09-11.json](SFT_V19_OUTPUT_REVIEW_2026-09-11.json), [SFT_V19_PAIRED_METRICS_2026-09-11.json](SFT_V19_PAIRED_METRICS_2026-09-11.json), [SFT_V20_CHECKPOINT_COMPARISON_2026-09-11.json](SFT_V20_CHECKPOINT_COMPARISON_2026-09-11.json), [SFT_V20_OUTPUT_REVIEW_2026-09-11.json](SFT_V20_OUTPUT_REVIEW_2026-09-11.json), [SFT_V20_RELOAD_LAUNCH_2026-09-11.json](SFT_V20_RELOAD_LAUNCH_2026-09-11.json), [SFT_V20_RELOAD_RESULT_2026-09-11.json](SFT_V20_RELOAD_RESULT_2026-09-11.json), [SFT_V22_CHECKPOINT_ARCHIVE_2026-09-12.json](SFT_V22_CHECKPOINT_ARCHIVE_2026-09-12.json), [SFT_V22_DPO_COMPARISON_2026-09-12.json](SFT_V22_DPO_COMPARISON_2026-09-12.json), [SFT_V22_EXECUTION_2026-09-12.json](SFT_V22_EXECUTION_2026-09-12.json), [SFT_V22_OUTPUT_REVIEW_2026-09-12.json](SFT_V22_OUTPUT_REVIEW_2026-09-12.json), [SFT_V22_PAIRED_METRICS_2026-09-12.json](SFT_V22_PAIRED_METRICS_2026-09-12.json), [SFT_V2_COMPLETION_V17_RESULT.json](SFT_V2_COMPLETION_V17_RESULT.json), [SFT_V2_MICRO_V16_RESULT.json](SFT_V2_MICRO_V16_RESULT.json), [SFT_V2_PILOT_LAUNCH_2026-09-11.json](SFT_V2_PILOT_LAUNCH_2026-09-11.json), [SFT_V2_PILOT_PACKAGE_2026-09-11.json](SFT_V2_PILOT_PACKAGE_2026-09-11.json), [SFT_V2_PILOT_V19_LAUNCH_2026-09-11.json](SFT_V2_PILOT_V19_LAUNCH_2026-09-11.json), [SFT_V2_PREFLIGHT.json](SFT_V2_PREFLIGHT.json), [SFT_V2_READINESS_FINAL_2026-09-11.json](SFT_V2_READINESS_FINAL_2026-09-11.json), [SFT_V2_REVISION_CHECK.json](SFT_V2_REVISION_CHECK.json), [SFT_V2_SMOKE_INPUTS.json](SFT_V2_SMOKE_INPUTS.json), [SFT_V39_DPO_COMPARISON_2026-09-16.json](SFT_V39_DPO_COMPARISON_2026-09-16.json), [TERMINATION_MICRO_PROTOCOL_2026-09-11.json](TERMINATION_MICRO_PROTOCOL_2026-09-11.json), [TERMINATION_MICRO_V15_RESULT.json](TERMINATION_MICRO_V15_RESULT.json), [TOKENIZER_EOS_CANDIDATE_V1.json](TOKENIZER_EOS_CANDIDATE_V1.json).

### DPO

- [Filtrage du candidat DPO après revue contextuelle](DPO_FILTERING_2026-09-12.md)
- [Raccord du checkpoint courant au DPO](DPO_HANDOFF_2026-09-12.md)
- [Consolidation de la revue de projet du lot DPO v2](DPO_PROJECT_REVIEW_V2_2026-09-16.md)
- [Premier essai DPO sur le SFT courant — v27](DPO_V27_LAUNCH_2026-09-12.md)
- [Résultat du premier essai DPO — v27](DPO_V27_RESULT_2026-09-13.md)

Données de mesure associées : [DPO_CANDIDATE_REVIEW_2026-09-12.json](DPO_CANDIDATE_REVIEW_2026-09-12.json), [DPO_CONTEXT_SCAN_2026-09-12.json](DPO_CONTEXT_SCAN_2026-09-12.json), [DPO_CURRENT_SFT_ISOLATION_2026-09-12.json](DPO_CURRENT_SFT_ISOLATION_2026-09-12.json), [DPO_EXPERIMENT_DECISION_2026-09-12.json](DPO_EXPERIMENT_DECISION_2026-09-12.json), [DPO_FILTERED_CANDIDATE_2026-09-12.json](DPO_FILTERED_CANDIDATE_2026-09-12.json), [DPO_PREFLIGHT_LENGTHS_2026-09-12.json](DPO_PREFLIGHT_LENGTHS_2026-09-12.json), [DPO_REVIEWED_LOT_2026-09-12.json](DPO_REVIEWED_LOT_2026-09-12.json), [DPO_V22_REBIND_DECISION_2026-09-16.json](DPO_V22_REBIND_DECISION_2026-09-16.json), [DPO_V27_ARTIFACT_CHECK_2026-09-13.json](DPO_V27_ARTIFACT_CHECK_2026-09-13.json), [DPO_V27_RESULT_2026-09-13.json](DPO_V27_RESULT_2026-09-13.json), [DPO_V39_EXPERIMENT_DECISION_2026-09-16.json](DPO_V39_EXPERIMENT_DECISION_2026-09-16.json).

### Comparaison et évaluation

- [Audit de réalignement avec la mission OpenClassrooms](AUDIT_ALIGNEMENT_MISSION_2026-09-12.md)
- [Lancement de la comparaison Base / SFT / DPO v28](COMPARAISON_V28_LAUNCH_2026-09-13.md)
- [Comparaison commune Base / SFT / DPO — résultat v28](COMPARAISON_V28_RESULT_2026-09-13.md)
- [Comparaison finale QA — Base, SFT et DPO](FINAL_QA_V35_RESULT.md)
- [Replay des garde-fous de l'étape 2 — sorties v36](STAGE2_GUARDRAIL_REPLAY_V36_2026-09-16.md)
- [Évaluation de sûreté de l'étape 2 — v36](STAGE2_SAFETY_V36_RESULT_2026-09-16.md)
- [Gel de la réserve de triage synthétique v1](TRIAGE_RESERVE_V1_FREEZE_2026-09-16.md)
- [Consigne de triage partagée entre évaluation et API](TRIAGE_SHARED_PROMPT_2026-09-12.md)
- [Évaluation de développement du parcours de triage — v23](TRIAGE_V23_LAUNCH_2026-09-12.md)
- [Comparaison de triage v25 et correction de recharge](TRIAGE_V25_RESULT_2026-09-12.md)
- [Comparaison Base/SFT avec définitions explicites — v26](TRIAGE_V26_LAUNCH_2026-09-12.md)
- [Résultat v26 : effet de la consigne explicite](TRIAGE_V26_RESULT_2026-09-12.md)

Données de mesure associées : [COMPARAISON_V28_RESULT_2026-09-13.json](COMPARAISON_V28_RESULT_2026-09-13.json), [FINAL_QA_V35_RESULT.json](FINAL_QA_V35_RESULT.json), [STAGE2_GUARDRAIL_REPLAY_V36_2026-09-16.json](STAGE2_GUARDRAIL_REPLAY_V36_2026-09-16.json), [STAGE2_SAFETY_V36_RESULT_2026-09-16.json](STAGE2_SAFETY_V36_RESULT_2026-09-16.json), [TRIAGE_V25_RESULT_2026-09-12.json](TRIAGE_V25_RESULT_2026-09-12.json), [TRIAGE_V26_RESULT_2026-09-12.json](TRIAGE_V26_RESULT_2026-09-12.json).

### API et vLLM

- [Audit local des entrées et sorties de l'API](API_AUDIT_CONTENT_2026-09-12.md)
- [Audit : synchronisation et redémarrage local](AUDIT_RESTART_LOCAL_2026-09-14.md)
- [Preuve locale — collecte complémentaire explicite](COLLECTE_COMPLEMENTAIRE_LOCALE_2026-09-14.md)
- [Vérification locale du pilote de dialogue API](DIALOGUE_DRIVER_LOCAL_2026-09-14.md)
- [Lancement de l'intégration vLLM / API — v29](VLLM_API_V29_LAUNCH_2026-09-13.md)
- [Résultat v32 : intégration GPU vLLM et API](VLLM_API_V32_RESULT_2026-09-14.md)
- [Diagnostic v33 des réponses API rejetées](VLLM_API_V33_RESULT.md)
- [Résultat v34 : réponses complètes et limites de triage](VLLM_API_V34_RESULT.md)
- [Paquet vLLM/API v37 avec garde-fous](VLLM_V37_PACKAGE_2026-09-16.md)

Données de mesure associées : [VLLM_API_V32_RESULT_2026-09-14.json](VLLM_API_V32_RESULT_2026-09-14.json), [VLLM_API_V33_RESULT.json](VLLM_API_V33_RESULT.json), [VLLM_API_V34_RESULT.json](VLLM_API_V34_RESULT.json), [VLLM_IMAGE_MANIFEST_2026-09-13.json](VLLM_IMAGE_MANIFEST_2026-09-13.json), [VLLM_V37_PACKAGE_2026-09-16.json](VLLM_V37_PACKAGE_2026-09-16.json), [VLLM_V37_RESULT_2026-09-16.json](VLLM_V37_RESULT_2026-09-16.json).

### Déploiement et livrables

- [Garde-fous budgétaires du pilote Modal](MODAL_BUDGET_GUARDRAILS_2026-09-16.md)
- [Vérification du support de soutenance v47](PRESENTATION_V47_2026-09-16.md)
- [Vérification du rapport PDF v47](REPORT_PDF_V47_FINAL_2026-09-16.md)

## Archives

Le dossier [`archive/`](archive/) conserve les preuves qui ne sont plus citées par les points d'entrée du dépôt : paquets et lancements Kaggle, échecs vLLM v29–v31, échecs de comparaison v42 et de réserve v44–v45, brouillons de rapport PDF, vérifications de livraison locale, préparation de démonstration gratuite, protocoles SFT v2 intermédiaires et vérifications locales ponctuelles (Docker, audit API). Elles restent consultables pour la traçabilité et ne décrivent pas l'état courant.
