# Validation du protocole de triage expérimental

- **Date :** 2026-09-03
- **Statut :** proven pour le contrat technique ; not clinically validated
- **Code :** `bc398dd`
- **Protocole :** `educational-triage-protocol-v1`

## Claim vérifié

Le dépôt contient un protocole machine-readable qui autorise explicitement l'expérimentation scolaire tout en empêchant de déclarer une validation clinique, en imposant une politique conservatrice pour l'incertitude et en figeant le plan 4 000/500/500.

## Entrées et commande

```bash
PYTHONPATH=src .venv/bin/python scripts/validate_educational_protocol.py \
  --protocol configs/educational_triage_protocol_v1.json \
  --schema data/manifests/educational_triage_protocol_v1.schema.json
```

Environnement : Python 3.13 et `jsonschema` du projet.

## Résultat observé

- statut : `proposed_educational_only` ;
- validation clinique effectuée : `false` ;
- neuf familles de risque présentes ;
- total : 5 000 ;
- splits : 4 000 `train`, 500 `validation`, 500 `test` ;
- unité de split : `bilingual_group_id` ;
- SHA-256 du protocole : `87b811278459ce6a299481afac71188815e9bc5b6f4265a334b893efbdc39c97` ;
- SHA-256 du schéma : `75979975c16142cd14d8d5028d31ab935efb7850098835183db0da363ec8a903`.

Trois tests vérifient le protocole nominal, le refus d'une validation clinique déclarée et le refus de `deferred` comme conséquence du seul manque d'information.

## Frontière de preuve

**Prouvé :** cohérence et invariants du protocole technique versionné.

**Non prouvé :** exactitude médicale des règles, exhaustivité des signaux sévères, performance d'un modèle, acceptabilité clinique ou conformité réglementaire.
