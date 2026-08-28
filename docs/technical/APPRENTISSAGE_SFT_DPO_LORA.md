# Adaptation du modèle — LoRA, SFT et DPO

- **Date :** 2026-08-28
- **Statut :** proposed
- **Base prévue :** `Qwen3-1.7B-Base`
- **Périmètre :** stratégie d'adaptation définie par `CADRAGE_MISSION.md` et `SPEC_POC_TRIAGE_MEDICAL.md` ; aucune exécution d'entraînement à ce stade.

## Paramètres entraînables

La configuration visée charge Qwen avec ses poids d'origine gelés et injecte des adaptateurs LoRA dans des modules cibles à décider et versionner lors de la baseline. Seuls les paramètres de faible rang des adaptateurs sont optimisés :

```text
W' = W + scale × (B × A)
```

- `W` : matrice de poids pré-entraînée de Qwen, gelée ;
- `A` et `B` : matrices LoRA entraînables, de faible rang ;
- `scale` : facteur de mise à l'échelle défini par la configuration LoRA ;
- `W'` : poids effectif employés durant l'inférence avec l'adaptateur.

Le rang, l'alpha, le dropout, les modules cibles, la seed, le learning rate, le batch size et le nombre d'époques ne sont pas encore décidés. Ils devront être enregistrés avec chaque run ; aucune valeur ne doit être présentée comme validée avant expérimentation.

## Séquence d'entraînement prévue

```mermaid
flowchart LR
    A[Qwen base gelé] --> B[SFT sur exemples structurés]
    B --> C[Checkpoint LoRA SFT évalué]
    C --> D[DPO sur paires chosen / rejected]
    D --> E[Checkpoint LoRA DPO évalué]
    E --> F[Comparaison base / SFT / DPO]
```

Le SFT minimise l'écart entre la réponse générée et une cible de référence. Le DPO, depuis le checkpoint SFT accepté pour expérimentation, optimise une préférence relative entre `chosen` et `rejected`. Les deux étapes modifient les adaptateurs LoRA ; aucune ne modifie les poids de base gelés.

## Contraintes de reproductibilité et d'évaluation

- Sauvegarder le checkpoint/adaptateur, jamais seulement un nom de run.
- Associer au run les versions du modèle de base, tokenizer, datasets, transformation, prompt, code et dépendances.
- Évaluer base, SFT et DPO sur le même jeu isolé.
- Ne jamais choisir les hyperparamètres à partir du jeu `test`.
- Distinguer une amélioration de métrique automatique, une revue humaine et une validation clinique.

## Limite

Cette stratégie réduit le coût et facilite la comparaison ; elle n'établit ni conformité médicale ni sûreté clinique. Les critères d'acceptation devront être fixés avec les référents cliniques.
