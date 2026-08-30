# Audit UltraMedical-Preference v1

- **Date :** 2026-08-31
- **Statut :** implemented and observed on pinned revision
- **Sources :** `src/triage_poc/ultramedical_audit.py`, `scripts/audit_ultramedical_preference.py`, `scripts/audit_ultramedical_presidio_sample.py`

## Fonctionnement

L'audit lit les tableaux JSON avec `ijson`. Cette lecture en flux évite de charger le fichier `train` d'environ 1 Go en mémoire. Il vérifie les clés requises, les rôles conversationnels, la différence entre réponses choisie et rejetée, les métadonnées, les distributions de labels et modèles, les doublons de prompts et les chevauchements de split.

Les textes sont normalisés uniquement pour comparer leur égalité textuelle ; les rapports ne conservent que des hashes et des comptes. Le sample Presidio garde en mémoire les dix plus petits hashes par split, analyse les triples complets puis persiste uniquement les agrégats.

## Commandes reproductibles

```bash
PYTHONPATH=src .venv/bin/python scripts/audit_ultramedical_preference.py \
  data/raw/ultramedical-preference/data \
  > artifacts/ultramedical-preference-audit-2026-08-31.json

PYTHONPATH=src .venv/bin/python scripts/audit_ultramedical_presidio_sample.py \
  data/raw/ultramedical-preference/data \
  --sample-per-split 10 \
  > artifacts/ultramedical-preference-presidio-2026-08-31.json
```

## Entrées et sorties

- **Entrées :** `train.json`, `dev.json`, `test.json` à la révision du manifeste.
- **Sortie :** rapport JSON agrégé sans texte source.
- **Mémoire :** bornée par une ligne JSON, les compteurs de hashes et le petit sample Presidio.
- **Échec fermé :** l'absence de `dev` ou `test`, ou un JSON invalide, arrête l'audit.

## Limites

La normalisation ne détecte pas les paraphrases. La présence de plusieurs préférences pour un même prompt peut être intentionnelle et doit être regroupée, pas supprimée aveuglément. Le sample Presidio et les regex ne remplacent ni le scan du sous-ensemble retenu ni la revue clinique. Le test est un benchmark biomédical, pas une validation du contrat de triage du CHSA.
