# Consolidation de la revue de projet du lot DPO v2

- Date : 2026-09-16
- Statut : verified_for_educational_dpo
- Statut clinique : not_performed
- Sources : [manifeste compact](../../data/manifests/derived-ultramedical-dpo-v2-project-reviewed.json), [décision ADR-014](../decisions/ADR-014-essai-dpo-source-filtre.md), [preuve de revue parent](DPO_REVIEWED_LOT_2026-09-12.json), [manifeste SFT protégé](../../data/manifests/derived-source-medical-qa-sft-v2.1-reviewed.json).
- Environnement : macOS, worktree `codex/complete-poc-evaluation`, Python 3.13 du projet.

## Question vérifiée

Peut-on corriger la justification et la lignée du lot DPO sans modifier les textes,
les préférences sources, les splits ou la provenance utilisés par l'expérience DPO ?

## Transformation

`scripts/finalize_dpo_review.py` exige un lot parent déjà approuvé pour l'usage
éducatif, une décision de revue dont l'empreinte correspond au manifeste parent et
le manifeste SFT courant. Il refuse une ligne sans revue de confidentialité du POC
ou qui prétend une validation clinique.

Pour chaque ligne, il remplace la justification historique contradictoire
`project review pending` par une formulation qui conserve le `label_type` source,
borne l'admission à l'expérience éducative et dit explicitement qu'aucun professionnel
de santé n'a validé la préférence. Il ajoute l'identifiant et la date de la décision.

Les champs suivants sont comparés avant/après et doivent rester identiques :
`record_id`, `split`, `language`, `prompt`, `chosen`, `rejected`,
`source_label_type` et `source`.

## Chronologie et cohérence avec le SFT

Cette consolidation ne suit pas la création d'un nouveau corpus SFT. Le corpus SFT
v2.1 et ses splits existaient avant les entraînements : le checkpoint SFT 500 a été
entraîné sur le train de hash `70270d65…f4f9b` et évalué pendant le run sur la
validation de hash `554ee8ad…c74f25`. Sa configuration désigne le canonique v2.1
`687617f5…6567d` et consigne zéro exemple test utilisé.

Le DPO démarre ensuite depuis les poids de ce checkpoint SFT (`5c195a8c…a626d`) et
utilise un jeu distinct de préférences, ce qui est le fonctionnement attendu. Son
run est lié au manifeste de checkpoint `a39ba94d…38e1b` et le manifeste du lot DPO
protège le même canonique SFT `687617f5…6567d` contre les recouvrements de prompts.
La reprise du 16 septembre audite et documente cette chaîne ; elle ne remplace pas
les textes ou les splits qui ont servi aux entraînements.

## Résultat observé

- 426 lignes train et 54 lignes validation produites ;
- zéro justification contenant encore `pending` ;
- 480 décisions reliées à `ADR-014` ;
- 480 statuts cliniques conservés à `not_performed` ;
- 4 700 prompts SFT reliés à la protection contre le recouvrement ;
- zéro réponse du test SFT utilisée ;
- hashes et tailles du manifeste complet et des deux JSONL consignés dans le
  manifeste compact versionné.

La distribution source reste `easy=95`, `hard=194`, `length=191`. Ce sont des types
de labels UltraMedical, pas des degrés de qualité clinique établis par ce projet.

Commande de reproduction :

```bash
PYTHONPATH=src /path/to/project-python scripts/finalize_dpo_review.py \
  --source artifacts/dpo-reviewed-v1 \
  --output artifacts/dpo-reviewed-v2 \
  --sft-manifest data/manifests/derived-source-medical-qa-sft-v2.1-reviewed.json \
  --decision docs/evidence/DPO_REVIEWED_LOT_2026-09-12.json \
  --decision-id ADR-014 \
  --review-date 2026-09-12
```

Validation ciblée : dix tests DPO réussis, dont deux nouveaux tests de finalisation.
Ruff réussit sur le module, le CLI et les tests ajoutés.

## Portée de la preuve

Cette preuve établit la cohérence technique de la lignée et des statuts du lot DPO.
Comme les textes `prompt/chosen/rejected` sont identiques à la version parent, elle
n'impose pas de réentraînement du SFT ni du DPO déjà réalisé. Elle ne démontre ni
supériorité clinique des réponses choisies, ni anonymisation certifiée, ni alignement
des réponses françaises.
