# ADR-017 — Réentraîner sur le corpus final v2.2

- Date : 2026-09-16
- Statut : approved for educational POC
- Propriétaire : porteur du projet
- Statut clinique : not validated
- Sources : manifeste SFT v2.2, revue qualitative v37, ADR-016

## Contexte

Les checkpoints SFT et DPO historiques ont été produits avant la fermeture du corpus v2.2.
Ils ne peuvent donc pas être présentés comme issus du dataset final versionné. La revue v37
ne démontre par ailleurs aucun avantage qualitatif du DPO sur le SFT et montre encore des
faits non étayés et des textes corrompus dans toutes les variantes.

## Décision

Exécuter un nouveau SFT LoRA borné à partir de Qwen3-1.7B-Base sur les 3 721 lignes train
et 479 validation du manifeste v2.2. Conserver la seed, la recette, le tokenizer, les logs,
les checkpoints et les checksums. Comparer au run historique sans promettre de gain.

Si le SFT se charge, se recharge et satisfait ses contrôles techniques, exécuter ensuite un
DPO borné depuis ce checkpoint avec le lot UltraMedical v2 déjà revu. Ne modifier ni les
préférences ni les scénarios pendant cette comparaison.

## Alternatives écartées

- Livrer les anciens checkpoints comme s'ils provenaient de v2.2 : lignée fausse.
- Ajouter des labels de triage inventés au corpus QA : hors gouvernance et sans validation.
- Allonger immédiatement le DPO : aucun gain actuel ne justifie cette variable.
- Abandonner tout entraînement : incompatible avec le livrable SFT + DPO demandé.

## Conséquences

Le nouveau run corrige d'abord la reproductibilité du livrable. Une amélioration de loss,
de QA ou de sûreté devra être mesurée séparément. Si les défauts de triage persistent, la
roadmap distinguera données comportementales validées, prompt/garde-fous et préférences ;
elle ne les confondra pas avec davantage d'étapes sur la même source.
