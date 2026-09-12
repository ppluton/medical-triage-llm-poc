# Comparaison commune des modèles courants

- Date : 2026-09-12
- Statut : draft — runner implémenté ; exécution GPU non effectuée
- Sources : `scripts/run_current_comparison.py`, `configs/sft-v22-handoff.json`, `docs/evidence/TRIAGE_V26_RESULT_2026-09-12.md`.

## Protocole

La prochaine comparaison charge Base, SFT 500 et DPO dans le même processus
Transformers/PEFT, sans Unsloth. La quantification est celle du runner DPO
`BitsAndBytesConfig(load_in_4bit=True)` et sa configuration effective est archivée.
Le tokenizer SFT vérifié est commun. Désactiver les adaptateurs donne la Base ;
activer explicitement SFT ou DPO donne les deux autres variantes. Les poids chargés
sont comparés aux fichiers safetensors avant génération. Aucun entraînement.

Trois mesures identiques pour chaque variante :

- loss moyenne par exemple sur les 479 réponses de validation, prompt masqué ;
- génération greedy des 30 prompts QA figés de v22, plafond 512, EOS natif ;
- génération brute des 18 scénarios synthétiques de développement, consigne
  `triage-demo-v3-proposed`, mêmes paramètres et scoring strict sans réparation JSON.

Les entrées sont reliées aux manifestes et empreintes. Le test final n'est pas utilisé.
L'artefact DPO doit passer le vérificateur de sauvegarde avant admission. Les résultats
v26 restent un historique distinct, leur runtime Unsloth étant différent.

## Vérification locale et limites

Ruff et chargement CLI passent. Le tokenizer sauvegardé rend les 479 références avec
frontières prompt/réponse exactes et un EOS natif unique dans chaque réponse.
Ce contrôle ne prouve pas le fonctionnement CUDA ni l'égalité d'inférence après
recharge. La loss ne mesure pas la sûreté ; les générations brutes devront être relues
pour les faits inventés, sous-triages et questions inadéquates. Aucun gain n'est annoncé.

```sh
PYTHONPATH=src python scripts/run_current_comparison.py \
  --sft-manifest configs/sft-v22-handoff.json \
  --sft-adapter /path/to/verified-checkpoint-500 \
  --dpo-run /path/to/completed-source-dpo-v27 \
  --data-manifest data/manifests/derived-source-medical-qa-sft-v2.1-reviewed.json \
  --validation data/processed/source-sft-v2.1-reviewed/validation-qwen3.jsonl \
  --prior-qa /path/to/source-sft-v2-continuation-500/pilot_end.json \
  --scenarios data/samples/synthetic-triage-development-v2.json \
  --output /path/to/fresh-comparison
```

## Correction détectée avant exécution GPU

Le premier contrôle sur les 479 lignes a échoué : le rendu complet du chat template
sauvegardé se termine par `im_end`, alors que le SFT corrigé transforme explicitement
la fin de réponse en EOS natif. Le runner utilise désormais `render_prompt_completion`,
la même fonction que le pilote SFT, au lieu du helper historique `encode_example`.
Après correction : 479 frontières exactes, EOS natif final unique pour chaque réponse,
longueur maximale 939 tokens sur un budget 2 048. Aucun GPU n'a été lancé avec le
rendu incorrect et aucun résultat historique n'a été réécrit. Le runner DPO concatène
déjà chaque réponse avec l'EOS natif ; ce défaut concernait la nouvelle comparaison.
