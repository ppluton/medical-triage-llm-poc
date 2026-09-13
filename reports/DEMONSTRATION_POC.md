# Démonstration du POC de triage médical

- Date : 2026-09-13
- Statut : draft — déroulé préparé, démonstration avec modèle réel non exécutée
- Sources : `CADRAGE_MISSION.md`, `SPEC_POC_TRIAGE_MEDICAL.md`, rapport technique, scripts d'évaluation de l'endpoint et preuves v26/v27/v28.

## Déroulé de quinze minutes

| Temps | Démonstration | Preuve à afficher |
|---|---|---|
| 0–2 min | Besoin CHSA, collecte, questions complémentaires et priorité proposée ; responsabilité du professionnel | Mandat et limites du POC |
| 2–5 min | Sources de l'école, transformation corrigée, séparation train/validation/test, anonymisation et exclusions | Manifestes SFT et DPO, un exemple synthétique |
| 5–8 min | Base, SFT puis DPO : expliquer l'apprentissage et les résultats, y compris négatifs | Comparaison commune v28 terminée : montrer NLL, sorties valides et erreurs ; distinguer le runtime v26 |
| 8–12 min | Appeler l'API sur contexte incomplet, cas avec signal d'alerte et scénario anglais ; afficher questions, priorité et avertissement | Réponses du vrai modèle via vLLM, identifiant et version ; exécution encore à réaliser |
| 12–14 min | Retrouver l'interaction anonymisée dans l'audit et montrer latence et erreurs | Rapport de mesure et rapprochement JSONL, sans exposer token ni données réelles |
| 14–15 min | Limites et suite : jeu réservé, revue clinique, déploiement et conservation | État vérifié des livrables, sans annoncer une utilisation hospitalière |

## Conditions de la démonstration réelle

Retenir le checkpoint à partir des mesures comparables ; consigner son empreinte,
le prompt, la version du serveur et le code. Utiliser exclusivement les scénarios
synthétiques de développement. Le test final reste distinct de la répétition.
Le serveur cloud, son accès privé et son coût doivent avoir une cible autorisée.
Un appel au fournisseur simulé n'est pas une démonstration du modèle.

La mesure se fait avec `scripts/evaluate_triage_endpoint.py`, puis le rapprochement
avec `scripts/verify_endpoint_audit.py`. Le token passe par `TRIAGE_API_TOKEN`,
jamais dans une diapositive ou une commande publiée. Les rapports bruts restent
hors Git ; ne publier que les métriques et preuves expurgées.

Les mesures actuelles sont séquentielles et incluent les échecs : elles ne prouvent
pas un débit sous charge. Un JSON valide ne prouve pas une bonne priorité ; vérifier
aussi les informations inventées et les questions posées. Les priorités de référence
des scénarios restent proposées, sans validation clinique.

## État de préparation

DPO v27 terminé et fichier de poids vérifié. Comparaison v28 terminée et métriques
recalculées : NLL moyenne Base / SFT / DPO de 1,532 / 0,787 / 0,786 sur 479
validations ; JSON de triage conformes 0/18, 1/18, 1/18. La baisse de NLL ne
prouve ni justesse médicale ni amélioration du triage par DPO.

Le test privé vLLM/API v30 a chargé le modèle de base sur GPU, puis échoué
au démarrage de FlashInfer sur `cannot find -lcuda`. Le correctif du chemin
de liaison est enregistré dans `6f42e70` ; la version 31 est lancée pour le
vérifier. Ce lancement ne constitue pas une preuve de fonctionnement.
Inférence réelle de l'API, déploiement cloud et mesures associées encore non prouvés.
Ce déroulé est un support de préparation, pas une preuve de soutenance réalisée.

## Explication orale des résultats

« Le SFT apprend à mieux reproduire les réponses du corpus. Le DPO apprend à
préférer certaines réponses aux autres. Nous avons exécuté les deux étapes,
puis comparé les trois modèles sur les mêmes exemples. L’apprentissage améliore
la probabilité des réponses attendues, mais notre essai de triage produit encore
beaucoup de réponses incomplètes ou répétitives. Nous ne présentons donc pas ce
modèle comme prêt à trier des patients. Nous évaluons séparément la chaîne API,
ses contrôles, ses erreurs et sa traçabilité. »

Si la démonstration renvoie une erreur, montrer cette erreur et le journal
technique expurgé. Ne pas remplacer silencieusement la réponse par une sortie
préécrite ou par un autre modèle. Une capture d’une exécution antérieure doit
porter sa version et être présentée comme telle.
