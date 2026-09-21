# Évaluer le triage en complément des connaissances médicales

- Date : 2026-09-12
- Statut : draft — préparation et lancement, résultats en attente
- Source : [protocole de l'évaluation v23](../evidence/TRIAGE_V23_LAUNCH_2026-09-12.md).

Nous avons préparé dix-huit situations fictives couvrant les neuf familles du protocole en français et anglais. Le modèle Base et le SFT reçoivent les mêmes consignes. Le corrigé proposé reste en dehors de la question donnée au modèle.

Cette fois, nous observons directement une sortie de triage : priorité, synthèse, raisons, informations manquantes et questions complémentaires. Les réponses non conformes restent comptées. Retirer les erreurs avant de calculer le score donnerait une image trop favorable du système.

Il fallait aussi corriger notre instrument de mesure : deux anciens cas de démonstration contredisaient le protocole éducatif plus récent sur la gestion de l'incertitude. La nouvelle série applique le protocole existant, tout en conservant l'ancien jeu comme historique. Cela ne transforme pas les références proposées en avis médical validé.

L'expérience ne réentraîne rien. Elle recharge le SFT, vérifie qu'il reproduit les réponses enregistrées, puis mesure son comportement. La présence de questions ne prouve pas leur pertinence ; un bon JSON ne prouve pas une bonne décision. Nous lirons les sorties avant de décider de la suite.

## Mise à jour du 12 septembre : contrôler aussi l'évaluateur

L'évaluation v23 s'est arrêtée car seules 14 réponses rechargées sur 30 étaient
identiques. Cela ne dit pas que le corpus est à refaire. Une différence concrète
existe dans notre programme : l'ordre de chargement des bibliothèques diffère de
celui de l'entraînement, et Unsloth émet un avertissement à ce sujet.

Nous rétablissons l'ordre connu et conservons les réponses détaillées lors du
prochain contrôle. L'idée est de tester une cause précise en gardant les poids et
les questions constants. Les tests locaux vérifient que le diagnostic sait montrer
une différence ; seule l'exécution GPU peut vérifier que la recharge est fidèle.

## Mise à jour : pourquoi les poids peuvent être justes et les sorties différentes

La correction d'import ne résout pas la recharge (v24 : 14/30 identiques). Une
bibliothèque d'inférence peut garder une copie accélérée de certains poids. Si l'on
charge un nouvel adaptateur sans actualiser cette copie, le fichier est correct,
mais le calcul peut encore utiliser un état ancien. C'est une hypothèse sur notre
évaluateur, pas une nouvelle accusation du corpus.

La v25 mesure les copies obsolètes, vérifie les poids chargés puis réinitialise le
mode d'inférence comme le faisait le script SFT. Le résultat GPU reste nécessaire
pour confirmer ou réfuter cette explication. Les tests CPU prouvent seulement que
notre diagnostic sait reconnaître une copie qui ne correspond plus au poids.
