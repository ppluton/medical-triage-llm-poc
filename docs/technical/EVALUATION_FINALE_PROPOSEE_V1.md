# Protocole proposé du test final

- Date : 2026-09-13
- Statut : proposed — pas encore figé ni exécuté
- Sources : SPEC_POC_TRIAGE_MEDICAL.md, configs/final-evaluation-proposed-v1.json, COMPARAISON_MODELES_COURANTS.md.

## Question et conditions

Après les décisions de développement sur validation, comparer Base, SFT et DPO
sur le split réservé. Ne pas consulter ses réponses pour choisir checkpoint,
prompt ou hyperparamètres. Avant exécution, figer ces choix, les hashes des poids,
du tokenizer, du code, des entrées et du runtime dans un manifeste distinct.
La configuration proposée ne lance rien et ne sélectionne encore aucun exemple.

## Mesures prévues

Calculer la loss sur réponse seule et EOS natif pour les 500 exemples, avec le
même rendu que le SFT et la comparaison v28. Rapporter moyenne par exemple,
comptage, longueur et éventuels dépassements ; aucun exemple exclu silencieusement.
Pour borner la génération, sélectionner 50 identifiants par ordre croissant du
SHA-256 UTF-8 de `42:<record_id>`, puis identifiant en cas d'égalité. Vérifier
l'unicité des identifiants et conserver la liste avant toute génération. Ce choix
ne dépend ni de la réponse attendue ni des résultats d'un modèle.

Générer les mêmes 50 prompts pour les trois variantes, greedy, plafond 512 tokens.
Conserver textes, IDs de tokens, arrêt EOS, répétitions et temps. Les 50 exemples
ne garantissent pas une représentation équilibrée des langues ou sources : publier
leur composition, sans les remplacer a posteriori. La loss et l'arrêt ne sont pas
une mesure de justesse médicale. Une revue des réponses reste nécessaire ; ne pas
utiliser un score lexical comme substitut à cette revue.

Les 18 scénarios de triage déjà utilisés restent des scénarios de développement.
Les rejouer avec l'API teste l'intégration, pas la généralisation à un test inédit.
Le test QA réservé n'apporte pas de labels de priorité clinique. Toute revendication
de performance clinique reste exclue sans protocole et références cliniques validés.

## Exécution et suites

Le runner v28 impose actuellement 479 validations et les 30 prompts historiques :
il ne doit pas être réutilisé en renommant le test en validation. Adapter explicitement
le runner et son vérificateur au manifeste final avant de lancer ce protocole.
Vérifier d'abord la fin et les résultats de v28, puis le budget gratuit disponible.
Une correction motivée par les résultats du test rend ce jeu utilisé pour le
développement ; ne pas conserver alors la qualification de test indépendant.
