# Comparaison commune Base / SFT / DPO — résultat v28

- Date : 2026-09-13
- Statut : draft — exécution terminée, métriques recalculées, qualité insuffisante
- Sources : COMPARAISON_V28_RESULT_2026-09-13.json, COMPARAISON_V28_LAUNCH_2026-09-13.md, artefacts privés Kaggle v28 (`349471067`).

## Mesures observées

La CLI Kaggle confirme COMPLETE. Les quatre JSON et le journal sont téléchargés
sous `artifacts/kaggle/current-comparison-v28-reports`. Le vérificateur
`verify_current_comparison.py` recalcule les métriques sur les entrées 479/30/18
figées ; leurs hashes et les populations des trois variantes correspondent.
Aucun entraînement ni exemple de test réservé utilisé. Le journal se termine
vers 3 940 secondes, environ 65,7 minutes pour le notebook entier.

| Mesure commune | Base | SFT 500 | DPO v27 |
|---|---:|---:|---:|
| NLL réponse moyenne, 479 validations | 1,532125 | 0,786970 | 0,786059 |
| QA arrêt EOS, sur 30 | 23 | 26 | 27 |
| JSON triage conforme, sur 18 | 0 | 1 | 1 |
| Priorité conforme avec JSON valide, sur 18 | 0 | 1 | 1 |
| Cas critiques avec JSON valide et maximum, sur 6 | 0 | 0 | 0 |
| Triage atteignant le plafond de 512 tokens | 9 | 17 | 17 |

Les réponses QA SFT et DPO sont textuellement identiques sur 29/30 prompts ;
les réponses de triage sur 12/18. La légère baisse de NLL DPO (environ 0,12 %)
ne prouve pas un gain de justesse. Le seul scénario de triage conforme pour les
deux adaptateurs est `dev-triage-v2-vulnerability-fr`, classé moderate.

## Lecture qualitative et limites

Des réponses répétitives atteignent le plafond avant fermeture JSON. Exemple SFT,
`chest_pain-en` : le modèle ajoute âge, antécédents et traitements non fournis,
puis les répète. Des réponses DPO conservent aussi des affirmations non fournies,
notamment sur le scénario d'informations insuffisantes. Ces observations réfutent
l'idée que la baisse de loss suffirait à rendre le triage utilisable.
Les sorties invalides sont des échecs dans le dénominateur ; le score des seuls
JSON valides ne doit pas être présenté comme une réussite générale.

Le runtime commun est Transformers 4.57.6, PEFT 0.18.1, Torch 2.10.0+cu128,
bitsandbytes 0.50.2 ; quantification FP4 sans double quantification, calcul 4-bit
float32. La v26 utilisait Unsloth et obtenait 12/18 JSON conformes pour le même
SFT. Ce changement de runtime/quantification empêche d'attribuer directement
la différence au DPO. L'effet causal du backend reste non isolé.

## Décision suivante

Conserver ces résultats négatifs. Ne pas promouvoir le DPO ni relancer un SFT long
sur leur seule base. Vérifier directement les modèles dans la chaîne vLLM/API cible, sur les
scénarios synthétiques de développement, puis choisir le runtime de démonstration. Le test réservé reste fermé pendant
ces décisions. La validation clinique, l'API avec vrai modèle et le déploiement
restent non prouvés. Aucune exposition publique n'est autorisée par cette mesure.
