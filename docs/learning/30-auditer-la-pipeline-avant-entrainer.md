# Auditer la pipeline avant de réentraîner

- **Date :** 2026-09-05
- **Statut :** draft
- **Sources :** ADR-011 ; PIPELINE_AUDIT_V1.json ; SFT_LABEL_AUDIT_V14.json ; scripts de pré-vol et tests du dépôt.

## Ce qui a été fait

Nous avons remonté la chaîne depuis les sorties répétitives du SFT jusqu'aux exemples sources, au tokenizer et aux labels réellement reçus par le trainer. L'audit Kaggle v14 n'a exécuté aucune étape d'entraînement. La préparation locale a été corrigée pour conserver les choix des QCM, éviter les coupures de texte et protéger les anciens splits.

## Pourquoi cela était nécessaire

La loss mesure la capacité à prédire les tokens de référence. Elle ne garantit pas que le modèle saura produire une réponse autonome puis s'arrêter. Le SFT v5 avait une meilleure loss et des générations dégradées. Entraîner plus longtemps sans comprendre cette divergence aurait consommé du quota sans preuve de progrès.

## Comment

L'audit compare les hashes, le contenu canonique et les conversations rendues. Il tokenise le texte exact, avec les marqueurs du template. Dans le trainer Kaggle, il inspecte les labels après préparation et collation : 0 EOS natif par exemple dans le format initial, 1 dans le format candidat. Les marqueurs de début et fin ont les mêmes embeddings gelés ; cela rend leur discrimination impossible avec la projection de sortie liée observée.

La reconstruction ajoute les options avant anonymisation et rejette les exemples trop longs. Une nouvelle version protège la reproductibilité de v1. Les identifiants déjà rencontrés gardent leur split, même si des exemples sont rejetés et remplacés. Un test construit de vrais enregistrements synthétiques avec le producteur puis les valide contre le schéma v2 : il a permis de corriger une divergence de liste des transformations.

## Notions à retenir et questions ouvertes

- Le tokenizer, le template et le checkpoint constituent un ensemble à sauvegarder et vérifier ensemble.
- Un EOS dans le fichier n'est pas encore la preuve d'un EOS supervisé : la collation peut masquer ou transformer les labels.
- Changer la sélection des données peut déplacer silencieusement des exemples entre train et test. Il faut préserver les affectations historiques.
- Un pré-vol bloquant évite de découvrir les erreurs après plusieurs heures de GPU.
- La prochaine preuve manquante est un petit entraînement suivi de générations et d'une recharge du checkpoint. L'effet sur les répétitions et le contenu reste à mesurer.
- Les corpus de questions médicales ne fournissent pas une validation du triage. Le DPO et la démonstration API ont leurs propres contrôles.

## Résultat de la reconstruction

Les 5 000 exemples v2 ont été reconstruits. Les 101 anciennes lignes tronquées sont remplacées, les 4 899 identifiants conservés gardent leur split, et aucun choix ne manque dans les 2 250 QCM de développement contrôlés. Les 4 500 rendus respectent le contexte et se terminent par EOS. Ces preuves permettent de préparer un micro-run ; elles ne disent pas encore si le modèle corrigé répondra mieux.
