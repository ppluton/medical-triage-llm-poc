# Audit MEDIQA 2019 v1

- **Date :** 2026-08-31
- **Statut :** implemented and observed on pinned revision
- **Sources :** `src/triage_poc/mediqa_audit.py`, `scripts/audit_mediqa.py`, `scripts/audit_mediqa_presidio_sample.py`

## Fonctionnement

L'inventaire parcourt les XML des tâches RQE et QA. Pour le test, l'export labellisé est canonique et sa copie non labellisée reste visible dans le rapport sans être recomptée. La sortie contient uniquement des agrégats : volumes, distribution des labels, doublons normalisés, placeholders, motifs email/téléphone et erreurs XML.

Le contrôle Presidio sélectionne de façon déterministe dix questions par fichier canonique à partir du hash du chemin et de l'identifiant source. Il analyse les questions en anglais et ne persiste ni le texte, ni les spans, ni les valeurs détectées. Les longues réponses QA ne sont pas couvertes par ce sample.

## Commandes reproductibles

```bash
PYTHONPATH=src .venv/bin/python scripts/audit_mediqa.py \
  data/raw/mediqa2019 > artifacts/mediqa-candidate-audit-2026-08-31.json

PYTHONPATH=src .venv/bin/python scripts/audit_mediqa_presidio_sample.py \
  data/raw/mediqa2019 \
  --sample-per-file 10 \
  > artifacts/mediqa-presidio-sample-2026-08-31.json
```

## Entrées et sorties

- **Entrée :** checkout Git MEDIQA épinglé à la révision du manifeste.
- **Sortie :** rapport JSON agrégé, sans texte source.
- **Échec fermé :** l'absence de XML arrête l'inventaire ; un XML malformé est compté et empêche de considérer le format comme entièrement valide.

## Limites

La normalisation détecte seulement les doublons textuels, pas les paraphrases. Les regex ne déterminent pas si un numéro est institutionnel ou personnel. Le sample Presidio ne couvre ni toutes les questions ni les réponses. Enfin, aucun label MEDIQA ne représente une priorité clinique.
