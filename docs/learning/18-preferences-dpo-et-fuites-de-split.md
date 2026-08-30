# Préférences DPO : le volume ne compense pas une fuite de split

- **Date :** 2026-08-31
- **Statut :** observed
- **Sources :** `docs/evidence/ACQUISITION_AUDIT_ULTRAMEDICAL_PREFERENCE_2026-08-31.md`, `docs/decisions/ADR-005-reconstruire-les-splits-dpo-ultramedical.md`

## Ce qui a été fait

Nous avons téléchargé les trois splits d'UltraMedical-Preference à une révision précise, vérifié les fichiers, audité 112 362 paires en lecture en flux et passé 30 triples complets dans Presidio.

## Pourquoi cette étape était nécessaire

Le DPO apprend au modèle à préférer une réponse à une autre. Si un même prompt se trouve dans l'entraînement et dans le test, la mesure finale n'est plus indépendante. Le modèle peut avoir optimisé exactement le cas que nous prétendons évaluer.

## Comment cela a été réalisé

Chaque prompt a été normalisé puis hashé. Nous avons comparé les ensembles de hashes entre splits sans conserver les textes dans le rapport. Cette méthode a exposé 30 prompts communs entre l'entraînement et le test et 1 228 entre l'entraînement et la validation.

## Notions à retenir

- Le DPO nécessite un prompt, une réponse choisie et une réponse rejetée.
- Une préférence biomédicale générale n'est pas automatiquement une préférence de sûreté de triage.
- Le benchmark humain doit rester hors entraînement.
- Plusieurs paires pour un même prompt peuvent être utiles, mais elles ne comptent pas comme plusieurs scénarios indépendants.
- Un audit en flux permet de traiter un gros fichier sans saturer la mémoire.

## Prochaine étape

Implémenter la reconstruction déterministe définie par l'ADR-005, produire les comptes et hashes des splits nettoyés, puis construire un sous-ensemble DPO lié au contrat de triage. Le DPO restera postérieur au SFT : il ne remplace ni la création des scénarios de triage ni leur validation clinique.
