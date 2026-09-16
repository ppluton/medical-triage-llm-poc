# Sélection du modèle et ouverture unique de la réserve

- Date : 2026-09-16
- Statut : `executed_negative_result`
- Statut clinique : aucune validation clinique
- Sources : `scripts/verify_current_comparison.py`, `scripts/prepare_current_comparison_review.py`, `scripts/select_current_candidate.py`, `scripts/run_selected_reserve.py`, `scripts/build_kaggle_selected_reserve.py`

## Objet

Cette chaîne empêche l’évaluation finale de devenir une nouvelle boucle de réglage. Elle
sépare quatre opérations : vérification des observations de développement, revue qualitative
aveugle, sélection du candidat, puis ouverture unique de la réserve synthétique gelée.

## Entrées et contrats

La comparaison Base/SFT/DPO doit être terminée avec zéro étape d’optimisation, zéro ligne de
test et la validation comme split d’évaluation. Les métriques sont recalculées depuis les
observations sauvegardées. Les sorties de triage qui respectent le schéma commun aux trois
variantes sont placées dans une file seedée où l’identité du modèle est séparée dans une clé.
Les échecs de schéma restent visibles dans la couverture et ne sont pas transformés en succès.

La décision retient DPO uniquement s’il domine SFT au sens de Pareto : aucune régression sur
les métriques techniques et les quatre catégories de revue qualitative, avec au moins une
amélioration stricte. À égalité ou en présence d’un compromis, le SFT vérifié est retenu. Cette
règle est une politique d’ingénierie conservatrice ; elle ne constitue pas un seuil clinique.

Le fichier de décision contient le SHA-256 exact du résumé de comparaison et affirme que la
réserve n’a pas été utilisée. Le runner final refuse une décision différente, une comparaison
ayant utilisé le test, un manifeste de réserve modifié ou une autre variante que SFT/DPO.

## Exécution finale prévue

`build_kaggle_selected_reserve.py` produit un notebook privé T4 qui monte trois ressources
Kaggle privées et versionnées : Base, SFT v39 et DPO v41. Il n’utilise aucune ancienne sortie
de notebook comme dépendance. Avant tout chargement GPU, `verify_base_snapshot` contrôle le
manifeste et les checksums du snapshot Base. Le runner charge ensuite uniquement l’adaptateur
sélectionné pour générer les dix-huit réponses de la réserve.

Les sorties enregistrent les identités Base/SFT/DPO, paramètres de génération, versions de
packages, métriques, latences et empreintes de sélection/réserve. Elles portent explicitement
la règle `do_not_tune_or_rerun_from_this_result`.

## Vérifications observées avant exécution

- tests ciblés de sélection, réserve, revue aveugle et snapshot : réussis ;
- régression locale `val_367e616fcded` : 230 tests réussis, deux avertissements connus ;
- lint `val_6c2ea378668a` : réussi ;
- ressource DPO privée prête : `pierrepluton/chsa-dpo-v41-policy-ae66169e-apache2`.

## Limites

L’unicité du run est une règle de protocole et de versionnage, pas un mécanisme de sécurité
impossible à contourner. La réserve reste synthétique, ses références sont proposées et sa
revue finale n’est pas clinique. La v46 exécute finalement cette chaîne sur le SFT retenu.
Elle confirme 0 JSON conforme sur 18, 17 plafonds de génération et une répétition moyenne de
0,8289. Le résultat est figé sans réglage ultérieur ; voir
`docs/evidence/SELECTED_RESERVE_V46_RESULT_2026-09-16.md`.
