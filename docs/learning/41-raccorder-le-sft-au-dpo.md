# Passer le bon modèle à l'étape suivante

- Date : 2026-09-12
- Statut : draft
- Source : [preuve du raccord DPO](../evidence/DPO_HANDOFF_2026-09-12.md).

Nous avons remplacé une référence fixe à l'ancien SFT par un manifeste qui identifie le modèle choisi et son tokenizer. Le tokenizer est le dictionnaire et le format de lecture du modèle : transmettre les bons poids avec un autre format pourrait fausser l'expérience.

La vérification compare les empreintes des fichiers et relie la comparaison Base/SFT au même modèle. Des tests s'assurent qu'un fichier modifié ou la comparaison d'un autre checkpoint sont refusés. Le contrôle effectué sur les vraies paires DPO confirme également qu'elles tiennent dans la longueur disponible, sans couper les réponses.

Ce travail répare un raccord technique. Il ne prouve pas encore que DPO améliore le modèle : cela nécessite la revue des préférences, un entraînement et une comparaison. Nous conservons ces étapes distinctes pour avancer sans transformer une préparation réussie en résultat inventé.

La première lecture du lot rappelle pourquoi cette distinction compte : une réponse peut être préférée pour son explication alors que les deux réponses choisissent la même option. Les préférences sélectionnées sont anglaises et les réponses choisies sont souvent plus longues. On ne peut donc pas annoncer à l'avance qu'elles rendront l'assistant plus bref, meilleur en français ou compétent en triage ; ce sont des effets à mesurer.
