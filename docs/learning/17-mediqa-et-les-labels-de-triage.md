# MEDIQA : une source réelle n'est pas encore un dataset de triage

- **Date :** 2026-08-31
- **Statut :** observed
- **Sources :** `docs/evidence/ACQUISITION_AUDIT_MEDIQA_2026-08-31.md`, `docs/decisions/ADR-004-mediqa-comme-source-de-comprehension.md`

## Ce qui a été fait

Nous avons acquis une version précise de MEDIQA 2019, vérifié sa licence, inventorié les tâches RQE et QA, mesuré les doublons et testé 70 questions avec Presidio. Les données brutes restent hors Git.

## Pourquoi cette étape était nécessaire

Le brief demande de partir de sources réelles. Cela signifie conserver leur provenance et leur rôle exact, pas leur attribuer artificiellement les labels dont nous avons besoin. Une paire RQE répond à « ces deux questions ont-elles le même sens ? ». Un score QA répond à « cette réponse est-elle pertinente ? ». Aucun des deux ne répond à « quelle priorité de triage faut-il attribuer ? ».

## Comment cela a été réalisé

Nous avons épinglé le commit Git, calculé le checksum d'une archive reproductible, choisi une politique canonique pour éviter de recompter les exports de test et créé deux scripts : un inventaire complet sans texte source et un audit Presidio déterministe sur un échantillon.

## Notions à retenir

- Une source réelle peut servir de matière documentaire sans fournir la cible du modèle.
- Un label ne peut être réutilisé que si sa signification correspond au contrat cible.
- Les splits et les doublons doivent être maîtrisés avant la sélection.
- L'anonymisation automatique réduit le risque, mais ne remplace pas la revue humaine.

## Questions ouvertes

- Quelles questions MEDIQA sont assez proches des scénarios de triage du brief ?
- Quel référent clinique validera les niveaux et recommandations dérivés ?
- MEDIQA doit-il servir au SFT, à une évaluation auxiliaire, ou aux deux avec des enregistrements strictement séparés ?

## Prochaine étape

Auditer le schéma et un échantillon épinglé d'UltraMedical-Preference pour préparer le DPO, sans télécharger aveuglément le fichier d'entraînement d'environ 1 Go. En parallèle, formaliser la file de rédaction clinique qui transforme les sources réelles en scénarios synthétiques traçables, avec `triage_target: null` tant que la revue n'est pas approuvée.
