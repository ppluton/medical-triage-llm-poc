# ADR-014 — Essai DPO pédagogique sur les préférences sources filtrées

- Date : 2026-09-12
- Statut : approved for educational experimentation
- Propriétaire : porteur du projet ; mise en œuvre dans le périmètre déjà autorisé
- Revue technique : Codex, revue assistée ; aucune revue humaine indépendante revendiquée
- Statut clinique : not validated
- Sources : ADR-007, ADR-010, preuves DPO_FILTERING, DPO_CONTEXT_SCAN, DPO_CURRENT_SFT_ISOLATION, TRIAGE_V26_RESULT et DPO_CPU_MECHANICS du 12 septembre.

## Décision et périmètre

Poursuivre le cycle technique demandé avec un premier essai DPO borné à vingt étapes
sur le SFT général 500 et le lot UltraMedical filtré de 426 train / 54 validation.
Les scores insuffisants du SFT sont la baseline expérimentale, pas un critère de
sûreté satisfait. La comparaison ultérieure conservera la consigne v26 et les mêmes
scénarios de développement ; le test final reste isolé jusqu'au gel des choix.

La décision d'usage éducatif des données repose sur les contrôles de provenance et
licence, la reconstruction des splits, le scan des identifiants directs, le scan
contextuel de tous les champs du candidat initial, la revue des récits personnels,
leurs exclusions, puis la lecture des alertes restantes et de contextes ambigus.
Les 95 récits personnels non vérifiés et une paire altérée ont été exclus. Aucun
texte ni label de préférence des 480 paires retenues ne sera modifié pour cette admission.

Les statuts `approved_for_educational_dpo` désignent cette décision technique
limitée. Ils ne signifient ni certification d'anonymisation, ni exactitude scientifique
exhaustive, ni revue clinique. `clinical_review_status` reste `not_performed`.
Les préférences restent biomédicales sources, entièrement anglaises, avec des limites
de représentativité et de généralisation au français. Elles ne deviennent pas des
paires de priorités cliniques approuvées.

## Écart au mandat et limites

L'exigence de préférences validées cliniquement n'est pas satisfaite par cette revue.
Cet écart reste un livrable de gouvernance ouvert ; il ne doit pas disparaître du
rapport final. La décision n'autorise aucune utilisation patient ni exposition publique.
Un DPO réalisé peut améliorer, laisser inchangés ou dégrader les résultats. Aucun
seuil arbitraire de QCM ni nouvelle durée de SFT n'est introduit comme préalable.

## Conditions d'exécution

Notebook privé existant `pierrepluton/chsa-source-sft-qwen3`, T4 gratuite uniquement.
Vérifier les hashes du SFT/tokenizer, du lot, de la comparaison et de cette décision.
Conserver référence identique au départ et inchangée à l'arrivée, vérifier des poids
policy modifiés et finis, archiver les sorties et contrôler la sauvegarde/recharge.
Une erreur technique conserve le statut de run échoué ; elle n'est pas transformée
en résultat DPO. Réexaminer les données si un nouvel identifiant personnel est découvert.
