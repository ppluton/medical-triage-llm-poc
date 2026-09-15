# Checklist de revue clinique v1

- **Date :** 2026-09-16
- **Statut :** proposed — protocole de validation du POC ; aucune revue professionnelle indépendante revendiquée
- **Sources :** spécification du POC, corpus de l'étape 1, lot DPO UltraMedical-Preference

Dans la mission OpenClassrooms, le CHSA et ses équipes sont fictifs : aucun référent clinique externe n'est fourni. Chaque exemple destiné au DPO ou à l'évaluation reçoit donc une revue de POC traçable avant le statut `approved_for_educational_dpo` ou `validated_for_poc_evaluation`. Ce statut ne signifie jamais « approuvé par un professionnel de santé ».

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
- identité/rôle du réviseur de projet ; les qualifications professionnelles ne sont renseignées que si elles sont réelles et vérifiables ;
- date, version du protocole et langue de la revue ;
- exactitude médicale de `chosen` et `rejected`, chacune notée séparément ;
- sécurité, complétude, hallucinations, prescription ou fausse assurance éventuelles ;
- pertinence de la préférence pour le triage, qui peut être `not_applicable` ;
- justification clinique écrite de la préférence ;
- décision finale `approved`, `rejected` ou `needs_revision`.

Une préférence `length`, `easy` ou `hard` fournie par UltraMedical ne devient pas une justification clinique. Une paire où `chosen` et `rejected` donnent la même conclusion mais diffèrent seulement par la longueur peut être utile à une préférence de style, pas automatiquement à la sûreté du triage.

## Porte de lot

Le lot DPO peut porter le statut de projet `approved_for_educational_dpo` lorsque toutes les lignes retenues ont une décision associée, que les empreintes correspondent et qu'un résumé enregistre les comptes par décision, le protocole, les réviseurs et les exclusions. Le champ `clinical_review_status` reste `not_performed` tant qu'aucun professionnel de santé n'a réellement participé : cette valeur est une limite honnête, pas un motif pour arrêter le POC scolaire.

Un statut tel que `clinically_reviewed` ou `approved_by_healthcare_professional` est interdit sans revue professionnelle réelle. Cette seconde porte concerne une expérimentation clinique ou hospitalière future.
