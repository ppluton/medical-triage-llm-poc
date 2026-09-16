# Vérification du PDF provisoire du rapport

- Date : 2026-09-16
- Statut : verified_draft_render
- Source : `reports/RAPPORT_TECHNIQUE_POC.md`
- Sortie locale : `output/pdf/rapport-technique-poc-chsa-draft.pdf`
- SHA-256 : `0b043c1f75bd70bb0b3aef120def83ab1332c4a83c3c2b16a4b109d9ca61c156`

Le générateur ReportLab produit six pages A4, sous la limite de vingt pages. Les six
pages ont été rendues en PNG avec Poppler puis inspectées : aucun chevauchement, texte
coupé, carré noir ou tableau illisible n'a été observé. Le pied de page
`Brouillon - POC pédagogique, sans validation clinique` et la pagination sont présents
sur chaque page. L'extraction textuelle confirme l'absence de marqueurs Markdown `###`
résiduels et la présence des sections v2.2, v39, 215 tests et conditions de clôture.

Le générateur masque désormais les chemins Markdown locaux dans le rendu tout en gardant
les libellés humains. Le PDF reste un brouillon : il doit être régénéré après les résultats
DPO, l'évaluation de réserve et la décision cloud. Il ne remplace pas le futur fichier final
nommé selon l'identité et le mois de démarrage confirmés par Pierre.
