# Validation locale de la livraison v46

- Date : 2026-09-16
- Statut : verified_local
- Environnement : macOS, Python 3.13.14, pytest 8.4.2
- Réservation de validation : `val_b3af388b1647`

## Commandes

```bash
.venv/bin/python -m pytest
.venv/bin/python -m ruff check src scripts tests
shasum -a 256 output/pdf/rapport-technique-poc-chsa-v46-final.pdf \
  output/pptx/poc-triage-medical-chsa-v46.pptx
pdfinfo output/pdf/rapport-technique-poc-chsa-v46-final.pdf
unzip -t output/pptx/poc-triage-medical-chsa-v46.pptx
```

## Résultats observés

- `235 passed` en 12,15 secondes ; deux avertissements de dépréciation Starlette/AnyIO ;
- Ruff : `All checks passed` ;
- PDF : cinq pages A4, SHA-256
  `5ac3e90ae78632f8e1c1493e62b55d3d5fc30e7ad15aed8cf5d3b3fd5fe82d1d` ;
- PowerPoint : archive OOXML valide, SHA-256
  `fd8db31a76141448fb10d98e08e7a075a5866dd179f2f4c85b33ca8508c80844`.

Cette validation prouve la non-régression locale de la suite, la conformité statique Python et
l'intégrité des deux candidats de livraison. Elle ne prouve pas l'exécution de GitHub Actions,
le déploiement cloud, l'accessibilité d'un endpoint, la qualité clinique ou la soutenance.
