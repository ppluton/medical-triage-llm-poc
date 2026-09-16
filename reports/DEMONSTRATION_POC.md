# Démonstration du POC de triage médical

- Date : 2026-09-16
- Statut : `final_candidate` — démonstration cloud exécutée sur deux scénarios synthétiques
- Sources : `CADRAGE_MISSION.md`, `SPEC_POC_TRIAGE_MEDICAL.md`, rapport technique, preuves SFT v39/v40, DPO v41, comparaison v43, réserve v46, API v34/v37, Modal et Cloudflare.

## Déroulé de quinze minutes

| Temps | Démonstration | Preuve à afficher |
|---|---|---|
| 0–2 min | Besoin CHSA, collecte, questions complémentaires et priorité proposée ; responsabilité du professionnel | Mandat et limites du POC |
| 2–5 min | Sources de l'école, transformation corrigée, séparation train/validation/test, anonymisation et exclusions | Manifestes SFT et DPO, un exemple synthétique |
| 5–8 min | Base, SFT puis DPO : expliquer l'apprentissage, la sélection conservatrice du SFT et le résultat négatif final | Comparaison de développement v43 puis réserve v46 ouverte une seule fois : 0/18 JSON conforme |
| 8–12 min | Rejouer, sur une cible autorisée, l'API gardée sur contexte incomplet, signal d'alerte et scénario anglais ; afficher questions, priorité et avertissement | API v34/v37 : sortie contrainte, garde-fous, identifiant et version ; ne pas présenter cette conformité comme une capacité du modèle brut |
| 12–14 min | Retrouver l'interaction anonymisée dans l'audit et montrer latence et erreurs | Rapport de mesure et rapprochement JSONL, sans exposer token ni données réelles |
| 14–15 min | Limites et suite : triage, revue clinique, déploiement et conservation | État vérifié des livrables, sans annoncer une utilisation hospitalière |

## Conditions de la démonstration réelle

Utiliser le SFT v39 retenu avant ouverture de la réserve ; consigner son empreinte,
le prompt, la version du serveur et le code. Utiliser exclusivement des scénarios
synthétiques de démonstration distincts de la réserve finale désormais figée.
Le serveur cloud, son accès privé et son coût doivent avoir une cible autorisée.
Un appel au fournisseur simulé n'est pas une démonstration du modèle.

Le frontend public de soutenance est `https://triage-poc.pierrepluton.com`. Son accessibilité,
son certificat et son raccord à Modal sont observés. Le proxy refuse les mauvais tokens et
transmet les appels autorisés à l'endpoint GPU. Deux scénarios synthétiques FR/EN ont produit
une réponse gouvernée puis une trace d'audit rapprochée.

L'interface `/demo` sert de poste de démonstration : sélectionner le scénario français de
douleur thoracique, lancer l'évaluation, commenter la priorité, les informations manquantes,
la latence et l'identifiant d'audit ; basculer ensuite sur le scénario neurologique anglais.
Le token est saisi au début de la session et n'est ni conservé par le navigateur ni montré au
public. Le contrat `/docs` complète la preuve d'intégrabilité, sans remplacer le parcours réel.

La mesure se fait avec `scripts/evaluate_triage_endpoint.py`, puis le rapprochement
avec `scripts/verify_endpoint_audit.py`. Le token passe par `TRIAGE_API_TOKEN`,
jamais dans une diapositive ou une commande publiée. Les rapports bruts restent
hors Git ; ne publier que les métriques et preuves expurgées.

Les mesures actuelles sont séquentielles et incluent les échecs : elles ne prouvent
pas un débit sous charge. Un JSON valide ne prouve pas une bonne priorité ; vérifier
aussi les informations inventées et les questions posées. Les priorités de référence
des scénarios restent proposées, sans validation clinique.

## État de préparation

Le SFT v39 et le DPO v41 sont terminés, rechargeables et vérifiés. Sur le développement v43, la NLL Base/SFT/DPO vaut 1,532/0,830/0,829. Le DPO termine mieux et répète moins, mais ajoute un signal diagnostic ou prescriptif dans la revue aveugle ; il n'est donc pas retenu. Cette sélection ne prouve aucune pertinence clinique.

La réserve v46, ouverte une seule fois sur le SFT choisi, produit 0/18 JSON conforme, 17/18 sorties au plafond et 18/18 sorties signalées comme malformées ou répétitives. Ce résultat est figé : il n'a déclenché aucun réglage ni nouvel entraînement. Le modèle brut ne peut pas être le produit de démonstration.

L'API v34 produit néanmoins 18/18 réponses conformes par adaptateur grâce au schéma contraint et aux garde-fous, avec 8/18 priorités correspondant aux références pédagogiques proposées. Elle n'utilise pas le niveau intermédiaire et les cas incomplets restent faibles. La v37 confirme l'exécution Base/SFT/DPO et deux dialogues FR/EN ; les garde-fous interviennent fréquemment. La démonstration doit donc porter sur une chaîne gouvernée et non sur une autonomie du modèle.

La démonstration publique est établie sur deux cas synthétiques : douleur thoracique en français et déficit neurologique en anglais. Les deux appels ont retourné `maximum`, utilisé le fallback sûr v3 et été retrouvés dans l'audit privé. Cette preuve ne couvre ni la charge, ni la disponibilité continue, ni une validation clinique. Ce déroulé reste un support ; le test final QA ne sert pas à répéter la démonstration.

## Explication orale des résultats

« Le SFT apprend à mieux reproduire les réponses du corpus. Le DPO apprend à
préférer certaines réponses aux autres. Nous avons exécuté les deux étapes,
puis comparé les trois modèles sur les mêmes exemples de développement. Le DPO
améliore certaines métriques de forme, mais pas assez pour compenser une régression
qualitative ; nous avons donc retenu le SFT avant d'ouvrir la réserve. Sur cette
réserve, le modèle brut échoue au contrat de triage. Nous ne le présentons pas comme
prêt à trier des patients. La démonstration porte sur la chaîne API, ses garde-fous,
ses erreurs, sa traçabilité et la décision humaine. »

Si la démonstration renvoie une erreur, montrer cette erreur et le journal
technique expurgé. Ne pas remplacer silencieusement la réponse par une sortie
préécrite ou par un autre modèle. Une capture d’une exécution antérieure doit
porter sa version et être présentée comme telle.
