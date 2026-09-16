# Une API qui répond ne suffit pas à prouver un bon triage

Date : 2026-09-14 — Statut : draft
Source : preuve v32 dans `docs/evidence/VLLM_API_V32_RESULT_2026-09-14.md`.

Nous avons chargé les modèles SFT et DPO dans vLLM et appelé la vraie API sur 18 scénarios synthétiques chacun. Cela était nécessaire pour mesurer le parcours complet : anonymisation, génération, validation, réponse et audit.

Le moteur a répondu aux 36 demandes. L’API a accepté 24 réponses et rejeté 12 réponses. Les 24 réponses acceptées possèdent une trace d’audit correspondante. Le premier résultat positif est donc une intégration réelle, avec des erreurs conservées au lieu d’être cachées.

Il faut distinguer trois questions : le serveur peut-il répondre, la réponse respecte-t-elle le contrat, et son contenu est-il pertinent ? Une sortie JSON valide peut encore répéter des phrases ou proposer une priorité inadéquate. Ici, les références pédagogiques correspondent à 6/18 réponses SFT et 5/18 DPO. Ces petits nombres ne valident aucun usage clinique.

La prochaine correction porte sur notre visibilité des erreurs : le message générique 502 protège les détails, mais ne permet pas de savoir quel contrôle a rejeté la réponse. Un code technique limité suffit pour diagnostiquer, sans enregistrer de texte sensible. Il reste ensuite à vérifier les erreurs précisément, l’évaluation finale et la démonstration déployée.

## Après la correction de génération

La v34 limite les répétitions et la taille des listes, avec davantage de place pour finir le JSON. Les deux modèles répondent maintenant aux 18 situations sans rejet, et les 36 réponses sont retrouvées dans l’audit. Pourtant, chaque modèle ne correspond qu’à 8 références proposées sur 18 : les six cas critiques et les deux cas non urgents. Le niveau moderate n’est jamais choisi. Cela illustre la différence entre réparer le format d’une réponse et améliorer son raisonnement de triage. Il reste à traiter ce parcours fonctionnel et à mesurer un jeu final isolé.
