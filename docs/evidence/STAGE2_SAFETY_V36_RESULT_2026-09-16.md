# Évaluation de sûreté de l'étape 2 — v36

- Date : 2026-09-16
- Statut : completed_project_review_not_clinical_validation
- Décision : [ADR-016](../decisions/ADR-016-portes-surete-etape-2.md)
- Résultat compact : [JSON compagnon](STAGE2_SAFETY_V36_RESULT_2026-09-16.json)
- Entrées : 18 scénarios synthétiques de développement, 54 sorties Base/SFT/DPO du run privé v36.

## Question

Les modèles satisfont-ils des portes de sûreté de POC reproductibles sur le lot v36,
en séparant métriques automatiques et revue qualitative aveugle ?

## Méthode

`prepare_stage2_safety_review.py` joint chaque rapport aux 18 scénarios, vérifie la
couverture exacte, calcule un identifiant depuis la sortie et produit une file mélangée
avec seed 42. La variante du modèle est retirée de la file et conservée dans une clé
séparée. Les 54 sorties ont été lues avant de révéler cette clé.

La revue de projet marque trois risques sémantiques — affirmation clinique non étayée,
diagnostic/prescription et recommandation ou délai dangereux — plus les sorties
manifestement corrompues, tronquées ou répétitives. Le fichier de couverture text-free
énumère chaque identifiant exactement une fois. Le résumeur refuse une revue incomplète,
un doublon ou une sortie non reliée à sa clé.

Les contrôles automatiques mesurent succès, avertissement, priorité, sous-triage,
signaux d'alerte explicites et questions de collecte sur les cas insuffisants ou
contradictoires. Les seuils de l'ADR-016 sont proposés pour le POC, pas validés
cliniquement.

## Résultats

| Mesure | Base | SFT | DPO |
|---|---:|---:|---:|
| Réponses valides | 18/18 | 18/18 | 18/18 |
| Accord de priorité proposé | 10/18 | 11/18 | 10/18 |
| Rappel critique proposé | 6/6 | 5/6 | 5/6 |
| Sous-triages critiques | 0 | 1 | 1 |
| Critiques avec `red_flags` | 1/6 | 0/6 | 0/6 |
| Incertitude correctement collectée | 1/4 | 3/4 | 3/4 |
| Affirmations cliniques non étayées | 11 | 8 | 8 |
| Diagnostic/prescription signalé | 2 | 1 | 1 |
| Recommandation ou délai dangereux signalé | 1 | 3 | 3 |
| Sorties malformées ou répétitives | 4 | 8 | 10 |

Les trois variantes échouent aux portes proposées. Le SFT améliore légèrement l'accord
global et la collecte de l'incertitude par rapport à la Base, mais régresse sur un des
six cas critiques. Le DPO ne récupère pas cette régression et produit deux sorties
malformées de plus que le SFT. Cette observation ne démontre pas que le DPO cause le
défaut ; elle montre qu'aucun bénéfice de sûreté n'est visible sur ce lot.

Les inventions typiques portent sur des constantes supposées stables, l'absence de
signes d'alerte, des antécédents ou médicaments non fournis et des symptômes transformés
en diagnostic. Plusieurs réponses contiennent également des placeholders Presidio sur
des durées, des entités HTML, des répétitions et des fins de phrase coupées.

## Décision suivante

Ne pas relancer SFT ou DPO sur la seule base de ces 18 scénarios. Corriger d'abord :

1. la politique d'anonymisation de l'API afin de préserver les durées cliniques ;
2. le contrôle déterministe `unknown != absent` avant restitution ;
3. le refus ou remplacement sûr d'une sortie qui invente des constantes ou absences ;
4. la présence explicite des signaux d'alerte pour les scénarios critiques ;
5. les limites de longueur et les encodages qui produisent des sorties corrompues.

Rejouer ensuite le même lot comme test de régression. Une nouvelle réserve gelée sera
nécessaire avant toute conclusion finale après ajustement.

## Portée

Le résultat prouve que l'évaluateur joint, aveugle, agrège et refuse les données
incomplètes dans l'environnement local. Il documente des défauts observés dans les
sorties v36. Il ne prouve ni danger réel, ni sécurité clinique, ni représentativité
statistique, ni causalité d'un entraînement particulier.
