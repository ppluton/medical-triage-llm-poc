# Génération du rapport PDF intermédiaire

- Date : 2026-09-13
- Statut : draft
- Sources : `reports/RAPPORT_TECHNIQUE_POC.md`, `scripts/build_report_pdf.py`.

## Périmètre et résultat

Le rapport Markdown est exporté en PDF A4 de 5 pages avec ReportLab.
Commande : `python scripts/build_report_pdf.py --source reports/RAPPORT_TECHNIQUE_POC.md --output artifacts/output/pdf/rapport-poc-brouillon-2026-09-13-v2.pdf`.
Le runtime utilisé est le Python fourni avec Codex, contenant ReportLab et pypdf.
Le fichier de sortie doit être nouveau ; le script refuse un écrasement.

- SHA-256 source : `4c7ab168e01e65b12b97d11babd1e8ecbcd71fae295132b11316dafdb66b10c8`.
- SHA-256 PDF : `e9e28e4b2d93e75563b2bf790de38cead28e2d8c44c4623bc4fe173652b0875f`.

Les cinq pages ont été rendues avec Poppler et inspectées visuellement : texte et
tableaux lisibles, aucun contenu coupé ou superposé, titres solidaires du paragraphe
suivant. Ruff valide le script. Le rendu Poppler aboutit malgré un avertissement
Fontconfig sur sa configuration système.

## Limites et prochaine étape

Ce contrôle prouve la génération et la lisibilité de ce brouillon uniquement.
Le convertisseur couvre les titres, paragraphes et tableaux utilisés par ce rapport ;
il ne constitue pas un moteur Markdown général. Le PDF reste hors Git.
La comparaison v28, le test réservé, la démonstration réelle et le déploiement
restent à intégrer avant de produire le livrable final. Cinq pages ne prouvent
pas que les exigences de fond sont satisfaites.
