# Résultat de la comparaison v43 — Base / SFT v39 / DPO v41

- Date : 2026-09-16
- Statut : `completed_project_review_not_clinical_validation`
- Notebook privé : `pierrepluton/chsa-source-sft-qwen3`, version 43
- Manifeste : `data/manifests/comparison-v43-review-v1.json`
- Décision : `configs/final-model-selection-v43.json`
- Optimisation : 0 étape
- Test et réserve utilisés : 0

## Intégrité et périmètre

Le run est terminé après environ 4 000 secondes. Les 479 losses, 30 générations QA et 18
scénarios de développement sont présents une fois par variante, dans le même ordre. Le
vérificateur local recalcule les métriques depuis les observations sauvegardées et confirme
les hashes des trois entrées. La Base, le SFT v39 et le DPO v41 sont évalués dans le même
processus quantifié 4 bits ; ces NLL ne doivent pas être comparées directement aux mesures
d’autres runners.

Le notebook monte le snapshot Base privé exact et le handoff SFT. Il ne répète toutefois pas
le préflight de checksum du snapshot avant chargement. Cette limite est explicite ; le runner
de réserve final appelle `verify_base_snapshot` et échoue avant chargement si un octet requis
diffère.

## Résultats QA de développement

| Variante | NLL moyenne | EOS / 30 | Plafond / 30 | Exact / 30 | Répétition 4-grammes |
|---|---:|---:|---:|---:|---:|
| Base | 1,532045 | 23 | 7 | 0 | 0,2682 |
| SFT v39 | 0,830098 | 24 | 6 | 5 | 0,1860 |
| DPO v41 | 0,828884 | 26 | 4 | 5 | 0,1420 |

DPO améliore légèrement la NLL, la terminaison et la répétition par rapport au SFT, sans
améliorer le nombre de correspondances exactes. Ces mesures décrivent la forme des trente
réponses de développement ; elles ne prouvent pas une meilleure réponse médicale.

## Triage brut de développement

| Variante | JSON valides / 18 | Accord toutes lignes | Maximum correct / 6 critiques |
|---|---:|---:|---:|
| Base | 0 | 0 | 0 |
| SFT v39 | 1 | 0 | 0 |
| DPO v41 | 1 | 0 | 0 |

Sans décodage contraint ni garde-fous, les trois modèles échouent donc à produire le contrat
attendu. Les sorties montrent des répétitions longues, des reprises du prompt, des faits
patient inventés et, dans l’unique JSON SFT/DPO valide, une priorité `moderate` pour une
détresse respiratoire proposée `maximum`. Cela confirme que l’API, le schéma contraint et les
garde-fous ne sont pas accessoires.

## Revue aveugle des 54 sorties

La file seed `143` contient toutes les sorties brutes, y compris les 52 invalides. L’identité
Base/SFT/DPO reste dans une clé séparée jusqu’à couverture des 54 décisions. La revue de projet
assistée utilise quatre flags bornés ; tout JSON invalide est signalé comme malformé.

| Variante | Signalées | Faits non étayés | Diagnostic/prescription | Délai dangereux | Malformé/répétitif |
|---|---:|---:|---:|---:|---:|
| Base | 18/18 | 0 | 1 | 1 | 18 |
| SFT v39 | 18/18 | 5 | 5 | 3 | 17 |
| DPO v41 | 18/18 | 5 | 6 | 3 | 17 |

Les comptes saturés reflètent surtout l’échec de génération structurée. DPO ajoute néanmoins
un flag diagnostic/prescriptif par rapport au SFT, sur une sortie de vulnérabilité qui invente
notamment un antécédent d’AVC et un traitement. L’assistance lexicale peut sur- ou sous-détecter
des formulations ; cette revue n’est pas clinique.

## Décision avant réserve

La règle versionnée exige que DPO ne régresse sur aucun critère suivi et progresse strictement
sur au moins un. DPO progresse sur quatre indicateurs de forme QA mais régresse sur un flag
qualitatif. Il ne domine donc pas SFT. **Le candidat retenu pour l’ouverture unique de la
réserve est le SFT v39 étape 150.**

Cette décision ne prétend pas que SFT est sûr ou cliniquement pertinent. Elle dit seulement que
le bénéfice DPO n’est pas assez uniforme pour justifier l’adaptateur supplémentaire. La réserve
reste non consultée au moment où cette décision et ses hashes sont enregistrés.
