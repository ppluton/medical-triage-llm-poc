# Lancement de la comparaison Base / SFT v39 / DPO v41

- Date : 2026-09-16
- Statut observé : `ERROR`
- Notebook privé : `pierrepluton/chsa-source-sft-qwen3`, version 42
- Optimisation : 0 étape
- Entrées : 479 validations QA, 30 générations QA, 18 scénarios synthétiques de développement
- Test et réserve finale utilisés : 0

Le paquet monte seulement le snapshot Base privé et le dataset SFT v39 privé. Il localise
le DPO v41 par le SHA-256 exact de son résumé et vérifie localement les poids avant lancement.
Les trente IDs QA sont embarqués sans leurs textes générés historiques. La validation v2.2
et les scénarios de développement sont séparés de la réserve finale.

Le statut `QUEUED` prouvait uniquement l'envoi. La version a ensuite échoué avant le
chargement du modèle à cause du module local `collection.py` absent du paquet. Voir la
[preuve d'échec v42](COMPARISON_V42_FAILURE_2026-09-16.md).
