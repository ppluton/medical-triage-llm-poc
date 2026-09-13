# Passer à la démonstration demandée

- Date : 2026-09-13
- Statut : draft
- Sources : mission OpenClassrooms, VLLM_API_V29_LAUNCH_2026-09-13.md.

Après la relecture des attendus, nous passons à l'intégration réelle du modèle.
Le diagnostic séparé NF4/FP16 n'est pas lancé. Le notebook v29 installe le moteur
vLLM, démarre l'API et mesure des requêtes synthétiques sur SFT puis DPO.

Cela permet de tester la chaîne du livrable : symptômes en entrée, réponse de
l'API, temps de réponse et journal associé. Les JSON sont contraints par le serveur ;
un meilleur respect du format ne suffira donc pas à affirmer un meilleur triage.
Les échecs seront conservés. Aucun résultat n'est encore disponible au lancement.

L'accès reste interne au notebook pour cette étape. Un endpoint accessible et
un déploiement GitHub Actions restent à concrétiser sur une cible autorisée.
