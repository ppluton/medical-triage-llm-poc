# Diagnostic v33 des réponses API rejetées

Date : 2026-09-14 — Statut : draft
Sources : manifeste compagnon VLLM_API_V33_RESULT.json ; run privé Kaggle v33 ; fournisseur instrumenté 1cb76f1, builder 51fcf8d.

La CLI confirme COMPLETE. Les deux lots donnent chacun 12 succès et 6 échecs sur 18 scénarios. Les 12 traces d’échec portent toutes `generation_incomplete`. Dans ce code, le fournisseur rejette la réponse lorsque `finish_reason` diffère de `stop`, avant validation JSON et anonymisation de sortie. La valeur exacte de finish_reason n’est pas enregistrée ; on ne peut pas affirmer sur cette seule preuve que chacune vaut `length`.

La configuration demande au maximum 512 tokens. Le diagnostic identifie l’étape responsable et écarte les erreurs de schéma ou d’anonymisation comme cause de ces rejets observés. Il ne prouve pas encore quelle modification de longueur ou de consigne les résoudra. Le refus doit rester en place : une réponse partielle ne devient pas acceptable parce qu’elle contient déjà une priorité.

Prochaine étape : mesurer les raisons exactes de terminaison et le nombre de tokens, avec une génération plus concise et un budget adapté, sur les scénarios de développement. Les poids et le test réservé restent inchangés. Aucun gain clinique n’est établi.
