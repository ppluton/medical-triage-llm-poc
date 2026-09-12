# Passer le bon modèle à l'étape suivante

- Date : 2026-09-12
- Statut : draft
- Source : [preuve du raccord DPO](../evidence/DPO_HANDOFF_2026-09-12.md).

Nous avons remplacé une référence fixe à l'ancien SFT par un manifeste qui identifie le modèle choisi et son tokenizer. Le tokenizer est le dictionnaire et le format de lecture du modèle : transmettre les bons poids avec un autre format pourrait fausser l'expérience.

La vérification compare les empreintes des fichiers et relie la comparaison Base/SFT au même modèle. Des tests s'assurent qu'un fichier modifié ou la comparaison d'un autre checkpoint sont refusés. Le contrôle effectué sur les vraies paires DPO confirme également qu'elles tiennent dans la longueur disponible, sans couper les réponses.

Ce travail répare un raccord technique. Il ne prouve pas encore que DPO améliore le modèle : cela nécessite la revue des préférences, un entraînement et une comparaison. Nous conservons ces étapes distinctes pour avancer sans transformer une préparation réussie en résultat inventé.

La première lecture du lot rappelle pourquoi cette distinction compte : une réponse peut être préférée pour son explication alors que les deux réponses choisissent la même option. Les préférences sélectionnées sont anglaises et les réponses choisies sont souvent plus longues. On ne peut donc pas annoncer à l'avance qu'elles rendront l'assistant plus bref, meilleur en français ou compétent en triage ; ce sont des effets à mesurer.

## Revue du 12 septembre : alerte n'est pas suppression

Le scan élargi des 576 paires détecte beaucoup de noms et de durées. Certains noms
sont des médicaments ou des protéines : les remplacer aveuglément dégraderait le
contenu médical. Nous conservons donc les alertes pour revue, sans modifier le lot.
Une pagination bibliographique a déjà subi un faux masquage dans une paire ; sa
correction ou exclusion doit être tracée plutôt que restaurer des chiffres supposés.

Nous avons aussi comparé les prompts DPO au corpus SFT corrigé : aucun doublon
exact normalisé. L'ancienne liste de protection était liée à la v1 et devra être
actualisée dans le manifeste final. Cette vérification n'utilise pas les réponses
du test final et ne détecte pas toutes les paraphrases.
