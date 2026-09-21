# Un scan PII n'est pas une validation

- Date : 2026-09-16
- Statut : draft
- Sources : [preuve du scan](../evidence/SFT_CONTEXTUAL_PII_SCAN_2026-09-16.md),
  [processus RGPD](../governance/PROCESSUS_RGPD_CORPUS_V1.md).

## Ce qui a été fait

Presidio a parcouru les deux champs textuels de chaque ligne du corpus SFT. Les résultats
détaillés restent privés ; le dépôt conserve une synthèse sans texte et une empreinte de
chaque artefact. Une seconde commande transforme les détections les plus prioritaires en
file de revue avec décision vide, plutôt qu'en suppression automatique.

## Pourquoi le résultat n'est pas simplement « oui/non »

Un nom détecté dans un corpus médical peut être celui d'un patient, mais aussi celui d'un
auteur, d'une maladie ou d'une institution. Une date peut être une durée utile au raisonnement.
Masquer chaque détection détruirait donc le corpus ; ignorer chaque faux positif apparent
laisserait un risque de confidentialité.

Le bon état intermédiaire est explicite : le scan est terminé, 22 lignes sont prioritaires,
3 180 demandent une revue contextuelle et aucune certification RGPD n'est revendiquée.

## À retenir

- détection, anonymisation et certification juridique sont trois choses différentes ;
- le texte sensible de revue ne doit pas entrer dans les preuves publiques ;
- une décision doit rester reliée à la ligne, à la source, au split et à l'empreinte ;
- le jeu de test peut être scanné pour la confidentialité sans devenir une donnée de réglage ;
- toute correction de texte crée une nouvelle version de données et impose de recalculer les
  contrôles d'intégrité et de séparation.
