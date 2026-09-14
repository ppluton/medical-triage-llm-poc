# Génération concise pour la démonstration

Date : 2026-09-14 — Statut : proposed
Sources : preuve VLLM_API_V33_RESULT.md, schéma ModelResult et fournisseur vLLM.

Les douze rejets de v33 surviennent avant la fin normale de génération. Le prompt v4 conserve la politique pédagogique proposée et tous les champs de réponse ; il demande de ne pas répéter les faits et limite le schéma de génération à deux éléments de 160 caractères par liste et un résumé de 240 caractères. Le contrat public reste inchangé. Le budget de génération passe de 512 à 768 tokens ; le runner GPU utilise un contexte de 4096 tokens. Les paramètres sont identiques pour SFT et DPO.

Cette combinaison vise une réponse courte et complète ; elle ne permet pas d’isoler séparément l’effet de la consigne et celui du budget. Elle ne démontre aucun gain de qualité avant exécution. Les traces distinguent désormais les raisons de terminaison connues length, content_filter et tool_calls avec des codes bornés ; aucune valeur arbitraire du fournisseur n’est journalisée.

Validation locale : 12 tests de serving réussis et Ruff réussi sur les modules modifiés. Les sorties incomplètes restent refusées. La prochaine preuve est la répétition des 18 scénarios synthétiques par adaptateur via le builder Kaggle ; ni poids ni test réservé modifiés.
