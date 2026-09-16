# Lire un pilote SFT sans surinterpréter la loss

- Date : 2026-09-16
- Statut : draft
- Sources : résultat SFT v39 et métriques appariées Base/SFT.

Le pilote v39 montre un apprentissage réel : les poids LoRA changent, la NLL validation
baisse et davantage de sorties rejoignent leur référence exacte. Cela ne signifie pas que
le modèle est devenu un meilleur agent de triage. Le corpus apprend surtout à répondre à
des questions médicales sources, sans labels de priorité clinique.

Les générations donnent l'information complémentaire essentielle : huit réponses MedQuAD
atteignent encore 512 tokens et plusieurs restent répétitives. Une décision fondée sur la
seule loss aurait donc masqué une faiblesse visible. La bonne lecture combine loss, arrêt,
répétition, inspection des sorties et preuve de recharge.

Enfin, un smoke de reprise valide la mécanique générale mais pas automatiquement le
checkpoint livré. Celui-ci doit être rechargé séparément avant de devenir la référence du
DPO. C'est le rôle strictement lecture seule de la v40.
