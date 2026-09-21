# Préparation de la revue pilote SFT 001

- **Date :** 2026-09-03
- **Statut :** proven pour la préparation technique ; revue humaine et clinique non commencées
- **Code :** `4fa05b1`
- **Run :** `sft-review-pilot-001-2026-09-03`

## Claim vérifié

Le pipeline peut sélectionner de façon déterministe 50 groupes bilingues représentatifs des neuf familles et des trois sources de la file v2, puis produire un formulaire local valide sans approuver automatiquement aucune décision.

## Résultat observé

Le lot séquentiel historique `review-batch-001.jsonl` contient 100 candidats `chest_pain`, 50 FR et 50 EN. Il n'est pas retenu comme pilote général.

Le nouveau pilote contient :

- 50 groupes et 100 identifiants candidats ;
- 21 groupes MedQuAD, 15 MediQAl et 14 FrenchMedMCQA ;
- 6 groupes douleur thoracique, 6 détresse respiratoire, 6 déficit neurologique, 6 vulnérabilité, 6 informations insuffisantes, puis 5 groupes pour chacune des quatre autres familles ;
- 50 décisions `pending` ;
- 0 validation clinique et uniquement l'action `manual_review_only`.

Le contrat JSONL local contient 50 lignes. Un export CSV éditable est produit avec les mêmes groupes et champs de revue. Leurs SHA-256 sont recalculés et consignés dans le manifeste.

## Validations exécutées

- tests unitaires du regroupement, de la reproductibilité, des statuts et du fail-closed ;
- Ruff ;
- validation des 5 000 entrées sources contre `sft_authoring_candidate_v1.schema.json` ;
- validation des 50 formulaires contre `sft_review_item_v1.schema.json` ;
- contrôle du SHA-256 d'entrée et de sortie.

## Limite de la preuve

Cette preuve porte sur la sélection et le contrat de revue. Elle ne prouve pas que les ancrages sont pertinents, que Presidio a éliminé toute PII, que les familles demandées conviennent, ni qu'une cible de triage est correcte. Ces décisions sont précisément l'objet de la revue à venir.
