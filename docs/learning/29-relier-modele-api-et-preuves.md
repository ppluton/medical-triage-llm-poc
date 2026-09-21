# Relier le modèle à une API vérifiable

- **Date :** 2026-09-05
- **Statut :** draft
- **Sources :** SPEC_POC_TRIAGE_MEDICAL.md, ADR-010, `src/triage_poc/api.py`, `src/triage_poc/serving.py`.

## Ce qui a été fait, pourquoi et comment

Le contrat FastAPI est étendu pour conserver les constantes, allergies et traitements, et retourner les questions complémentaires générées. Le fournisseur vLLM reçoit un contexte passé par Presidio et demande une sortie JSON conforme. Une réponse tronquée ou mal formée est refusée ; une panne d'anonymisation empêche l'appel réseau. L'API ajoute l'avertissement dans la langue de la requête et un identifiant d'interaction.

Les tests utilisent des scénarios synthétiques et un transport contrôlé. Ils montrent que notre code envoie et accepte le bon format, traite les erreurs et évite de copier le texte médical dans l'audit. Ils ne montrent pas qu'un modèle produit spontanément de bonnes questions ou qu'il choisit une priorité pertinente.

## Notions à retenir

Le conteneur API et le serveur GPU sont deux composants. Construire Docker ne prouve pas vLLM. Valider un schéma ne valide pas le contenu médical. Un audit minimal permet de retrouver version, résultat technique et latence, mais ne suffit pas à reconstruire le raisonnement clinique.

## Questions ouvertes

Le prompt demande la prudence sans établir une règle clinique validée. Il faut encore mesurer le comportement du modèle branché, définir les règles avec un référent, arrêter le contenu et la conservation de l'audit, et autoriser une cible privée de démonstration.
