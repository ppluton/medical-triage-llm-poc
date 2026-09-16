# Replay des garde-fous de l'étape 2 — sorties v36

- Date : 2026-09-16
- Statut : completed_historical_output_replay_not_new_inference
- Résultat compact : [JSON compagnon](STAGE2_GUARDRAIL_REPLAY_V36_2026-09-16.json)
- Entrées : 18 scénarios synthétiques et sorties sauvegardées Base/SFT/DPO du run v36
- Contrôles : `proposed-guardrails-v1`, API `0.4.0`, prompt candidat `triage-demo-v6-proposed`
- Statut clinique : aucune validation clinique.

## Question

Que feraient les nouveaux garde-fous sur les défauts observés en v36, avant de payer le
coût et le temps d'une nouvelle inférence GPU ou d'un nouvel entraînement ?

## Commande reproductible

```sh
PYTHONPATH=src python scripts/replay_stage2_guardrails.py \
  --scenarios data/samples/synthetic-triage-development-v2.json \
  --report base=artifacts/kaggle/api-dialogue-v36-reports/api-dialogue-candidate/base/endpoint.json \
  --report sft=artifacts/kaggle/api-dialogue-v36-reports/api-dialogue-candidate/sft/endpoint.json \
  --report dpo=artifacts/kaggle/api-dialogue-v36-reports/api-dialogue-candidate/dpo/endpoint.json \
  --output artifacts/stage2-guardrail-replay-v1.json
```

Le résumeur exige une couverture exacte des scénarios synthétiques et ne conserve aucun
texte de sortie dans le rapport agrégé. Les empreintes des entrées, du code et de l'artefact
privé sont enregistrées dans le JSON compagnon.

## Résultats observés

| Mesure après replay | Base | SFT | DPO |
|---|---:|---:|---:|
| Sortie modèle conservée | 3/18 | 3/18 | 2/18 |
| Sortie corrigée | 7/18 | 5/18 | 5/18 |
| Remplacement conservateur | 8/18 | 10/18 | 11/18 |
| Accord avec la priorité proposée | 16/18 | 16/18 | 16/18 |
| Rappel critique proposé | 6/6 | 6/6 | 6/6 |
| Critiques avec `red_flags` | 6/6 | 6/6 | 6/6 |
| Plancher de priorité sur l'incertitude | 4/4 | 4/4 | 4/4 |

Les métriques bornées de priorité progressent sur ce lot, mais au prix d'une forte
intervention : le modèle est restitué sans changement dans seulement 2 à 3 cas sur 18.
Cette fréquence est un signal de qualité insuffisante des générations, pas une réussite à
masquer. En particulier, 10 sorties SFT et 11 sorties DPO seraient remplacées entièrement.

## Ce que le replay prouve

Le code applique de manière déterministe les priorités minimales et les signaux d'alerte
définis dans la politique proposée. Il détecte sur les sorties historiques les signatures
pour lesquelles il a été écrit, remplace les contenus concernés et expose sa décision dans
l'audit. Les tests ciblés passent à 45 tests ; Ruff passe également.
La régression complète du dépôt passe à 196 tests en 45,41 secondes dans la réservation
`val_007b112e429f`, avec un avertissement externe Starlette/httpx déjà connu. Le contrôle
Ruff global sur `src`, `scripts` et `tests` passe.

## Ce qu'il ne prouve pas

Il ne s'agit pas d'une nouvelle inférence : le prompt v6, la politique d'anonymisation de
service et l'audit API 0.4.0 n'ont pas encore tourné avec les trois modèles sur GPU. Le lot
est un jeu de développement déjà consulté. Les détecteurs sont volontairement bornés et
peuvent manquer d'autres formulations inventées. Enfin, un fallback sûr selon la politique
proposée ne valide ni cette politique, ni le contenu médical, ni un usage auprès de patients.

## Décision suivante

Ne pas relancer immédiatement SFT/DPO. Emballer d'abord un candidat v37 avec API 0.4.0,
exécuter Base/SFT/DPO sur les mêmes scénarios comme régression technique, rapprocher les
audits puis analyser le taux de fallback. Ensuite seulement, décider si les erreurs restantes
relèvent des données SFT, des préférences DPO ou de la chaîne d'inférence. Une conclusion
finale exigera une nouvelle réserve isolée.
