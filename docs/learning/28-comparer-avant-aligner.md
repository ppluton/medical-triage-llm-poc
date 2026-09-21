# Comparer avant d'aligner

- **Date :** 2026-09-05
- **Statut :** draft
- **Sources :** preuve SFT Kaggle, ADR-010, COMPARAISON_POST_SFT_V1.md, documentation PEFT et TRL citée dans cette note technique.

## Ce qui a été fait

Nous avons construit une comparaison qui réutilise le même modèle, active ou désactive le LoRA, puis mesure les mêmes réponses de validation. Une préparation de candidats DPO et un script d'entraînement avec référence SFT figée complètent ce passage.

## Pourquoi

La baisse de loss pendant le SFT indique un ajustement, mais ne dit pas combien le SFT apporte par rapport à Base. Comparer deux environnements ou inclure une réponse attendue dans le prompt fausserait cette mesure. Consulter le test pour choisir le prochain entraînement finirait par transformer le test en validation.

## Comment et notions à retenir

Le tokenizer transforme chaque conversation en nombres. Le script vérifie où commence la réponse. La loss « réponse » ne compte que ses tokens ; la loss « séquence » inclut aussi le contexte. Nous additionnons les pertes et divisons par le nombre de tokens, pour ne pas donner artificiellement le même poids à des textes très courts et très longs.

Les générations sont séparées de ce calcul : elles commencent uniquement par les messages system et user. Elles doivent être lues pour détecter les changements de langue, répétitions, réponses incomplètes et affirmations non soutenues. Un score automatique n'accomplit pas cette revue.

Pour DPO, la référence est le SFT de départ. Désactiver simplement le LoRA pendant le calcul de référence utiliserait Base, ce qui changerait l'expérience. Deux adaptateurs initialement identiques permettent de garder l'un figé et de mettre à jour l'autre.

## Hypothèses et questions ouvertes

Les préférences UltraMedical portent sur des réponses biomédicales, pas nécessairement sur la prudence du triage. Presidio peut masquer des mots utiles. Il faut donc revoir les candidats, conserver les résultats négatifs et déterminer si des préférences spécifiques sont nécessaires. La comparaison de validation, le DPO réellement exécuté et la validation clinique restent trois preuves différentes.

## Retour de préparation des préférences

Le scan NER complet a dégradé les textes en confondant des termes biomédicaux avec des noms ou lieux. Le premier lot a été rejeté. La politique d'identifiants directs conserve mieux le contenu, mais ne couvre pas les noms, lieux et dates : elle impose une revue complémentaire. Même une pagination bibliographique peut être prise pour un téléphone. Une anonymisation qui passe ses contrôles automatiques n'est donc pas une preuve de données prêtes à entraîner.

## Résultat Base/SFT : une loss plus basse ne suffit pas

Sur les 500 validations, le SFT attribue davantage de probabilité aux références. Pourtant, les générations s'allongent jusqu'au plafond et certaines deviennent répétitives. Le teacher forcing mesure la probabilité du prochain token en donnant les précédents attendus ; une génération libre réutilise ses propres sorties. Les deux comportements ne sont donc pas interchangeables. Le diagnostic commence par les tokens de fin et la compatibilité du chargement, avant tout nouvel entraînement.

## Diagnostic de génération après la comparaison

Une loss de validation favorable ne garantit pas une réponse utilisable. Il faut effectuer quelques générations dès la première sauvegarde, puis comparer avec le modèle de base. Le diagnostic v10 conserve les identifiants des tokens : aucun marqueur de fin ne se trouve dans les trois sorties SFT tronquées. Configurer correctement le token d'arrêt est nécessaire mais ne peut pas arrêter sur un token que le modèle ne produit pas.

La prochaine expérience fait varier uniquement le chargement numérique (NF4 puis FP16), en gardant checkpoint, prompts et décodage identiques. Un résultat négatif doit rester visible et guider la recherche de cause avant un nouvel entraînement.
