# ADR-011 — Vérifier la pipeline avant un nouvel entraînement

- **Date :** 2026-09-05
- **Statut :** approved pour l'audit et les corrections locales ; expérimentation corrective proposée
- **Propriétaire :** porteur du POC
- **Statut clinique :** not validated
- **Sources :** demande utilisateur de vérifier la pipeline avant les entraînements longs ; CADRAGE_MISSION.md ; SPEC_POC_TRIAGE_MEDICAL.md ; PIPELINE_AUDIT_V1.json ; SFT_LABEL_AUDIT_V14.json.

## Contexte

La loss du SFT v5 diminue, mais ses 30 générations de contrôle atteignent la limite de 256 tokens. Le changement du critère d'arrêt, de quantification et de backend n'a pas corrigé les trois exemples diagnostiques. L'audit du trainer réel trouve zéro EOS natif supervisé dans chacun des 64 exemples inspectés. Les embeddings des marqueurs de début et fin de message sont identiques et gelés ; la base épinglée utilise une projection de sortie liée aux embeddings.

Les QCM ont également perdu leurs choix lors de la conversion. Le corpus v1 contient 101 exemples tronqués. Ces défauts justifient une correction des données et du format avant tout nouveau run long.

## Décision technique

1. Conserver le corpus v1 et le checkpoint v5 immuables comme références négatives.
2. Construire un corpus v2 séparé avec les choix sources, sans tronquer les questions ou réponses. Rejeter les exemples trop longs et compléter les quotas. Préserver le split de chaque identifiant déjà présent dans v1.
3. Utiliser un tokenizer candidat qui remplace uniquement le terminateur de la dernière réponse par l'EOS natif. Préserver le vocabulaire et les prompts de génération. Ce choix corrige une incompatibilité de format ; son effet sur la qualité reste à mesurer.
4. Refuser le pré-vol si le rendu exact dépasse le contexte, manque d'EOS terminal, mélange les splits ou utilise EOS comme padding.
5. Maintenir le blocage des entraînements longs et du DPO tant qu'un micro-run, ses générations et sa sauvegarde/recharge ne sont pas vérifiés.

## Portes de sortie

- Schéma et provenance cohérents, checksums vérifiés, choix conservés, absence de troncature, isolation historique des splits.
- Rendu exact et labels réels du trainer conformes ; aucun exemple test utilisé pour ajuster le modèle.
- Micro-run borné, poids effectivement modifiés, générations avant/après inspectées ; le tokenizer exporté conserve le format et le checkpoint rechargé reproduit les sorties déterministes.
- Comparaison Base/SFT sur un protocole versionné commun, puis revue des préférences DPO. Les scripts de comparaison v1 restent figés sur leurs anciens hashes ; un nouveau protocole est nécessaire pour v2.
- Inférence réelle via l'API, latence et audit vérifiés séparément avant démonstration.

## Alternatives et limites

Augmenter la durée du SFT ou lancer immédiatement le DPO risquerait de prolonger les défauts. Changer le modèle tout de suite empêcherait d'isoler les causes. Un micro-run peut prouver le fonctionnement technique ; il ne prouve ni une qualité suffisante ni une pertinence clinique. Aucun seuil clinique, déploiement ou publication n'est autorisé par cet ADR.
