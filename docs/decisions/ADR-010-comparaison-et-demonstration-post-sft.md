# ADR-010 — Comparaison post-SFT et démonstration privée

- **Date :** 2026-09-05
- **Statut :** proposed
- **Propriétaire :** porteur du POC
- **Statut clinique :** not validated
- **Sources :** CADRAGE_MISSION.md, SPEC_POC_TRIAGE_MEDICAL.md, ADR-008, preuve SFT du 2026-09-04 ; documentation PEFT et TRL 0.23.1.

## Contexte et périmètre

Le SFT est archivé, mais son gain n'a pas encore été mesuré. Les corpus de QA et les préférences biomédicales ne fournissent pas de priorités cliniquement validées.

## Proposition et conséquences

1. Comparer Base et SFT en 4 bits dans le même processus CUDA en activant ou désactivant l'adaptateur, avec le tokenizer sauvegardé et la révision de base épinglée. Mesurer les 500 références de validation, la loss séquence et la loss des seuls tokens de réponse. Les paramètres de génération sont communs ; les réponses sources ne sont jamais incluses dans le prompt de génération.
2. Réserver le test final à une comparaison figée après le DPO. Les scénarios déjà consultés restent des fixtures de développement. Ne pas utiliser les scores d'un test final pour choisir les paires DPO.
3. Garder les préférences UltraMedical `candidate` tant que leur préparation, anonymisation et revue ne sont pas terminées. Un entraînement technique sur des préférences proposées ne satisfait pas l'exigence de validation clinique de la spécification ; cet écart doit rester explicite.
4. Pour la démonstration, envoyer au serveur de modèle un contexte passé par Presidio et refuser toute réponse incomplète ou hors schéma. Une défaillance rend l'évaluation indisponible et indique le recours à un professionnel ; aucune priorité clinique n'est inventée comme valeur de repli.
5. Proposer un audit sans texte médical : identifiant, versions, statut et durée. Cette minimisation réduit l'information disponible pour un audit clinique et ne remplit pas encore la demande d'entrées anonymisées et de sorties auditables du brief. La politique de conservation et le contenu clinique de l'audit restent à décider.

## Alternatives

Rejouer le SFT avant comparaison ne résout pas l'absence de mesure. Mélanger les environnements Base/SFT introduit un facteur de confusion. Consigner les requêtes brutes est incompatible avec la minimisation attendue.

## Prochaine décision

Consigner les mesures Base/SFT et leur revue avant de lancer le DPO. Choisir la cible vLLM et le déploiement privé séparément. Aucune règle de triage ni seuil clinique n'est approuvé par cet ADR.
