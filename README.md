# POC Agent IA de triage médical

Projet d'étude public pour démontrer la faisabilité technique d'un assistant de triage initial. Il ne constitue pas un dispositif médical, ne pose aucun diagnostic et ne remplace jamais un professionnel de santé.

Les documents de référence sont [`CADRAGE_MISSION.md`](CADRAGE_MISSION.md), [`SPEC_POC_TRIAGE_MEDICAL.md`](SPEC_POC_TRIAGE_MEDICAL.md) et les règles de contribution dans [`AGENTS.md`](AGENTS.md).

## Démarrage local

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m spacy download fr_core_news_md
.venv/bin/python -m spacy download en_core_web_sm
.venv/bin/python -m pytest
```

Les données réelles ou brutes ne doivent jamais être ajoutées au dépôt. Les tests utilisent exclusivement des chaînes synthétiques.
