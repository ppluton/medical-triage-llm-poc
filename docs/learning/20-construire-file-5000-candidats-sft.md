# Construire une file de 5 000 candidats avant le SFT

- **Date :** 2026-08-31
- **Statut :** draft
- **Sources :** `CADRAGE_MISSION.md`, `SPEC_POC_TRIAGE_MEDICAL.md`, ADR-003, ADR-004, audits MedQuAD, MEDIQA 2019 et FrenchMedMCQA

## Ce qui a été fait

Une file locale de 5 000 tâches de rédaction a été construite à partir de 2 500 ancrages documentaires distincts. Chaque ancrage produit une tâche française et une tâche anglaise. La file contient 2 000 candidats issus de MedQuAD, 1 500 de MEDIQA 2019 et 1 500 de FrenchMedMCQA.

Ce volume n'est pas encore un dataset SFT. Aucun contexte patient, aucune réponse, aucun niveau de triage et aucun split n'ont été créés. Les 5 000 lignes sont explicitement marquées `training_eligible: false` et `clinical_review_status: not_started`.

## Pourquoi cette étape était nécessaire

Les sources du brief apportent des connaissances médicales, des questions, des réponses ou des préférences. Elles n'apportent pas automatiquement la décision de triage attendue. Copier leurs labels vers `maximum`, `moderate` ou `deferred` aurait fabriqué une vérité clinique que les jeux de données ne contiennent pas.

La file sépare donc deux objets :

1. l'ancrage documentaire, traçable jusqu'à une source et une licence ;
2. le futur scénario synthétique de triage, qui doit encore être rédigé, contrôlé et approuvé.

## Comment cela a été réalisé

- Les sources sont lues à leurs révisions déjà auditées.
- Les jeux `test` de MEDIQA et FrenchMedMCQA sont exclus de cette préparation.
- 1 000 ancrages MedQuAD, 750 MEDIQA et 750 FrenchMedMCQA sont sélectionnés dans un ordre déterministe fondé sur des empreintes SHA-256.
- Les questions identiques après normalisation lexicale sont dédupliquées dans chaque source.
- Presidio traite la question et la réponse avant leur persistance. Une détection résiduelle exclut l'ancrage et le quota est recomplété avec le suivant.
- Les extraits sont bornés à 4 000 caractères ; la troncature est signalée dans la ligne.
- Chaque ancrage est décliné en FR et EN, sans traduction automatique : la langue indique la tâche de rédaction attendue, pas la langue de la source.
- Cinquante paquets de 100 lignes rendent la revue humaine progressive.

## Notions à retenir

- **Candidat de rédaction ≠ exemple SFT.** Un exemple SFT exige une instruction et une cible approuvée.
- **Source-grounded ≠ cliniquement validé.** La provenance documentaire n'établit ni priorité ni sécurité clinique.
- **Bilingue ≠ traduit.** La file équilibre les tâches FR/EN ; la rédaction bilingue reste à faire.
- **Anonymisé automatiquement ≠ exempt de risque.** Presidio réduit le risque mais une revue humaine reste obligatoire.
- **Déduplication exacte ≠ déduplication sémantique.** Deux paraphrases peuvent encore représenter le même contenu.

## Hypothèses et questions ouvertes

- Les quotas par famille de risque sont `proposed` et servent uniquement à organiser la rédaction.
- La pertinence de chaque ancrage pour la famille demandée doit être revue avant rédaction.
- Le protocole clinique, les règles d'escalade et les seuils d'acceptation restent à approuver.
- La conversion finale en SFT devra regrouper les variantes d'un même scénario avant de créer les splits afin d'éviter les fuites.

## Prochaine étape pédagogique

Faire relire un premier paquet de 100 lignes, documenter les défauts de pertinence et d'anonymisation, puis ajuster le protocole de rédaction avant de traiter les 49 autres paquets. Aucun entraînement ne doit commencer sur cette file.
