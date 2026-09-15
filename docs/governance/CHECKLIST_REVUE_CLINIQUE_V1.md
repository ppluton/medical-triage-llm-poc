# Checklist de revue clinique v1

- **Date :** 2026-09-16
- **Statut :** proposed — aucune revue clinique indépendante enregistrée
- **Sources :** spécification du POC, corpus de l'étape 1, lot DPO UltraMedical-Preference

Chaque exemple destiné au SFT, DPO ou test doit être revu séparément par un référent clinique avant le statut `approved`.

- Le contexte est-il synthétique ou anonymisé de façon vérifiable ?
- Les informations manquantes et contradictions sont-elles explicitées ?
- La priorité attendue est-elle justifiée par un protocole approuvé ou marquée `proposed` ?
- La formulation évite-t-elle diagnostic, prescription et fausse assurance ?
- L'escalade vers un professionnel est-elle adaptée au scénario ?
- Pour une paire DPO, la préférence `chosen` est-elle motivée et la `rejected` clairement problématique ?
- Le scénario est-il isolé du jeu utilisé pour régler le modèle ?
- La source, le protocole, la date et le réviseur sont-ils enregistrés ?

Une checklist complète est une condition nécessaire, non une preuve que le POC est cliniquement validé.

## Décision minimale à enregistrer pour chaque paire DPO

La revue ne modifie jamais directement le JSONL source. Elle produit une décision séparée contenant :

- `record_id` et empreinte SHA-256 de la ligne revue ;
- rôle et identifiant professionnel du réviseur, conservés dans l'espace gouverné approprié ;
- date, version du protocole et langue de la revue ;
- exactitude médicale de `chosen` et `rejected`, chacune notée séparément ;
- sécurité, complétude, hallucinations, prescription ou fausse assurance éventuelles ;
- pertinence de la préférence pour le triage, qui peut être `not_applicable` ;
- justification clinique écrite de la préférence ;
- décision finale `approved`, `rejected` ou `needs_revision`.

Une préférence `length`, `easy` ou `hard` fournie par UltraMedical ne devient pas une justification clinique. Une paire où `chosen` et `rejected` donnent la même conclusion mais diffèrent seulement par la longueur peut être utile à une préférence de style, pas automatiquement à la sûreté du triage.

## Porte de lot

Le lot DPO peut porter le statut `clinically_reviewed` uniquement lorsque toutes les lignes retenues ont une décision associée, que les empreintes correspondent et qu'un résumé enregistre les comptes par décision, le protocole, les réviseurs et les exclusions. En l'absence de ce dossier, `clinical_review_status` reste `not_performed` ou `pending`.
