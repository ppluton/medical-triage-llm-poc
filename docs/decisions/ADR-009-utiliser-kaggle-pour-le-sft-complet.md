# ADR-009 — Utiliser un notebook Kaggle privé pour le SFT complet

- **Date :** 2026-09-04
- **Statut :** approved for educational implementation
- **Propriétaire :** porteur du projet d'étude
- **Statut clinique :** not validated
- **Sources :** micro-run SFT source-derived, stratégie d'exécution hybride, configuration SFT Kaggle

## Contexte

Le micro-run source-derived exécuté localement avec MLX a validé la chaîne technique, mais 20 étapes ont demandé environ 98 minutes. Une extrapolation directe rendrait le run complet de 1 000 étapes trop long pour le MacBook Air et mobiliserait la machine pendant une durée importante.

Le projet a besoin d'un GPU CUDA pour réaliser un entraînement pédagogique borné, sans engager immédiatement un service cloud payant ni publier le dataset ou les poids. Kaggle fournit un quota GPU gratuit, des notebooks versionnés, des logs et des sorties téléchargeables. Cette disponibilité reste une capacité opportuniste, pas une garantie de service.

## Décision

- Exécuter le premier SFT complet dans le notebook Kaggle privé `CHSA Source SFT Qwen3`.
- Conserver le dataset Kaggle `chsa-source-sft-v1` privé et exclure physiquement le split `test` du bundle d'entraînement.
- Exécuter un dry-run et un micro-run CUDA dans la même version avant d'autoriser le run complet.
- Utiliser un seul GPU Tesla T4 avec Unsloth, même lorsque l'interface annonce une allocation `T4 x2`.
- Entraîner Qwen3-1.7B Base en LoRA 4 bits pendant 2 epochs, soit 1 000 étapes attendues, avec une taille de batch effective de 8.
- Évaluer et sauvegarder toutes les 250 étapes, conserver au plus deux checkpoints et recharger le meilleur modèle selon `eval_loss`.
- Ne jamais pousser automatiquement les artefacts vers Hugging Face et ne jamais inclure de donnée patient, secret ou split `test`.
- Télécharger les sorties utiles et consigner leurs checksums avant de considérer le run comme archivé.

La configuration versionnée est `configs/source_sft_lora_kaggle.yaml`. Le résultat de l'exécution fera l'objet d'une preuve distincte : cette décision ne préjuge pas du succès du run.

## Alternatives considérées

### Continuer uniquement sur le MacBook Air

Cette option garde toutes les données localement et évite une dépendance cloud. Elle n'est pas retenue pour le run complet en raison de la durée observée du micro-run MLX. Le Mac reste utilisé pour la préparation, les tests courts, l'analyse et l'archivage.

### Utiliser Google Colab gratuit

Colab offre également des GPU temporaires. Kaggle est retenu pour ce premier run parce que le dataset privé, la version du notebook, les événements actifs, les logs et les outputs forment ici un parcours plus cohérent et déjà vérifié.

### Louer un GPU managé

Un service payant offrirait davantage de contrôle sur la capacité et la persistance. Il n'est pas nécessaire tant que le quota Kaggle suffit au POC borné. Cette alternative reste possible si les quotas gratuits, la durée maximale ou la disponibilité deviennent bloquants.

## Conséquences

- l'entraînement dépend temporairement de la disponibilité et des quotas Kaggle ;
- les données et artefacts doivent être gérés entre deux stockages distincts ;
- l'environnement CUDA diffère du micro-run MLX local et exige sa propre preuve technique ;
- les sorties lourdes restent hors Git ; seuls la configuration, les résumés, les checksums et les limites de preuve sont versionnés ;
- la comparaison Base/SFT devra utiliser le même jeu d'évaluation isolé pour éviter d'attribuer à Kaggle un gain qui vient d'un changement de protocole.

## Limites

- le run complet était encore en cours au moment de cette décision ;
- la durée finale, le checkpoint retenu et les losses finales ne sont pas encore observés ;
- la loss d'entraînement ou de validation ne mesure pas la qualité du triage ;
- ce choix d'infrastructure n'est ni une validation de sûreté ni une validation clinique.
