# ADR-003 — MedQuAD comme source de connaissance candidate

- **Date :** 2026-08-31
- **Statut :** approved for candidate processing only
- **Propriétaire :** équipe POC
- **Statut clinique :** not approved
- **Sources :** `data/manifests/src-medquad-577bd37.json`, `docs/governance/REGISTRE_SOURCES_DONNEES.md`, dépôt `abachaa/MedQuAD`

## Contexte

Le mandat vise environ 5 000 paires SFT de triage. MedQuAD fournit des questions-réponses médicales issues de sites NIH, mais ne contient ni priorité de triage, ni contexte patient complet, ni recommandation validée pour notre contrat.

L’audit de la révision épinglée a trouvé 47 441 paires, dont 31 034 réponses vides. Les réponses des sous-ensembles 10, 11 et 12 ont été retirées par les auteurs pour respecter le copyright MedlinePlus.

## Décision

- Conserver MedQuAD au statut `candidate`.
- Exclure les sous-ensembles 10, 11 et 12 et ne jamais recrawler leurs réponses.
- Utiliser éventuellement les neuf autres sous-ensembles comme sources de connaissance et de provenance pour rédiger des scénarios synthétiques.
- Interdire la conversion automatique d’une réponse QA en priorité ou recommandation de triage.
- Exiger une revue clinique séparée pour chaque scénario et cible avant admission au SFT.

## Raisons

Une réponse médicale générale peut informer la rédaction d’un scénario, mais elle ne définit pas une politique d’escalade. Inventer un niveau de triage à partir d’une QA transformerait une source documentaire en décision clinique non validée.

## Conséquences

Le dataset SFT de triage ne peut pas être obtenu par simple conversion de MedQuAD. Le projet doit créer une file de candidats synthétiques traçables, puis obtenir une revue clinique. Le volume final peut rester inférieur à 5 000 si les validations ne sont pas disponibles ; cette limite sera rapportée.
