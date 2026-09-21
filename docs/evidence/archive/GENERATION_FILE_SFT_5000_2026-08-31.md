# Preuve locale — génération de la file de 5 000 candidats SFT

- **Date :** 2026-08-31
- **Statut :** observed — technical evidence only
- **Sources :** code `facd3e4`, configuration `b3fe589812d8fe74559fc181d4a705d5d505c88845df7b4d1396d9d3c76eeea2`, manifestes de sources épinglés

## Claim vérifié

Le pipeline local peut produire exactement 5 000 tâches de rédaction bilingues, source-grounded et validées par schéma, tout en maintenant chaque ligne hors entraînement, sans cible de triage et sans split.

## Environnement et commande

- Machine : macOS arm64, environnement `.venv` du projet.
- Anonymisation : Presidio avec `fr_core_news_md` et `en_core_web_sm`.
- Code de génération : commit local `facd3e4`.
- Run : `sft-authoring-queue-2026-08-31`.
- Commande : commande intégrale documentée dans `docs/technical/FILE_REDACTION_SFT_5000_V1.md`.

## Résultat observé

| Mesure | Résultat |
|---|---:|
| Candidats | 5 000 |
| Groupes documentaires bilingues | 2 500 |
| Français / anglais | 2 500 / 2 500 |
| Candidats entraînables | 0 |
| Cibles de triage présentes | 0 |
| Splits présents | 0 |
| Lots de revue | 50 × 100 |
| Taille locale du paquet | 19 MiB |

Distribution par source : MedQuAD 2 000 candidats, MEDIQA 1 500, FrenchMedMCQA 1 500.

Contrôles de sélection et de confidentialité :

| Source | Ancrages retenus | Doublons exacts ignorés | Rejets PII résiduels | Extraits tronqués |
|---|---:|---:|---:|---:|
| MedQuAD | 1 000 | 11 | 9 | 26 |
| MEDIQA 2019 | 750 | 1 | 5 | 32 |
| FrenchMedMCQA | 750 | 6 | 33 | 0 |
| **Total** | **2 500** | **18** | **47** | **58** |

Empreintes :

- file JSONL : `26c18bbf7b4a885738118788ce585718ef7992b9b4be481eb765383d3bf7d571` ;
- index sans texte : `2a32e690d0ae7eb2a3ca7bf592713667ab24ba1171a711aacf9568186dbedb09` ;
- configuration : `b3fe589812d8fe74559fc181d4a705d5d505c88845df7b4d1396d9d3c76eeea2`.

La validation complémentaire a compté 5 000 lignes dans la file, 5 000 dans l'index et zéro ligne violant l'une des portes suivantes : `training_eligible: false`, `triage_level: null`, `split: null`, `clinical_review_status: not_started`.

## Ce que cette preuve établit

- Le générateur atteint le volume configuré avec une répartition bilingue exacte.
- Les artefacts sont traçables et leurs checksums sont enregistrés.
- Le pipeline exclut les détections PII résiduelles rencontrées et recomplète ses quotas.
- La structure empêche de confondre ces tâches avec des exemples SFT prêts à entraîner.

## Ce que cette preuve n'établit pas

- L'absence de toute donnée personnelle ou de tout faux positif d'anonymisation.
- La pertinence de chaque ancrage pour la famille de rédaction assignée.
- La qualité, la véracité ou la sûreté d'un scénario qui n'est pas encore rédigé.
- Une approbation clinique, juridique ou RGPD.
- L'existence de 5 000 paires instruction-réponse SFT.
- La permission de lancer un entraînement.

## Prochaine porte

Ouvrir un pilote de revue sur un lot de 100, enregistrer les décisions sans modifier le jeu d'évaluation, puis décider si les règles de rédaction et les quotas doivent être ajustés avant la suite.
