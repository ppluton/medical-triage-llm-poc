# Pourquoi MedQuAD ne devient pas directement notre dataset SFT

- **Date :** 2026-08-31
- **Statut :** observed
- **Sources :** `docs/evidence/ACQUISITION_AUDIT_MEDQUAD_2026-08-31.md`, `docs/decisions/ADR-003-medquad-source-de-connaissance.md`

## Ce qui a été fait

Nous avons téléchargé une version précise de MedQuAD, inventorié ses XML et testé un échantillon avec Presidio. Les données brutes restent hors Git et les rapports ne contiennent aucun texte source.

## Pourquoi cette étape précède le SFT

Une licence et un grand volume ne suffisent pas. Il faut savoir ce que les données enseignent réellement. MedQuAD répond à des questions médicales générales ; notre modèle doit produire une priorité, expliciter les informations manquantes et donner une recommandation encadrée.

Transformer automatiquement « réponse médicale » en « décision de triage » obligerait le programme à inventer la décision clinique que la source ne contient pas. Ce serait créer des labels non validés, pas nettoyer un dataset.

## Ce que nous avons appris

- 31 034 réponses sont vides ; trois sous-ensembles ont été volontairement amputés pour copyright.
- Les neuf autres sous-ensembles offrent 16 407 réponses non vides utilisables comme connaissance candidate.
- Les doublons et les détections PII nécessitent encore une sélection et une revue.
- MedQuAD peut soutenir la provenance d’un scénario synthétique, mais un professionnel doit valider la cible de triage.

## Prochaine étape

Une file documentaire équilibrée de 193 entrées anonymisées est maintenant disponible hors Git. Elle n’a volontairement aucun niveau de triage. La prochaine étape exige une contribution clinique : transformer certaines sources en scénarios synthétiques candidats, séparés du jeu d’évaluation, puis remplir la checklist de revue. Aucun candidat ne pourra entrer dans le SFT tant que sa revue n’est pas `approved`.
