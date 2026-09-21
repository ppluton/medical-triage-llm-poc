# Présentation du POC d’assistance au triage médical CHSA

- Date : 2026-09-21
- Statut : `final_candidate`
- Format : 14 diapositives 16:9, environ 12 minutes de présentation et 3 minutes de démonstration
- Support : `poc-triage-medical-chsa.pptx`, généré localement hors Git (`output/`), notes orales incluses
- Source unique des chiffres : [rapport technique](RAPPORT_TECHNIQUE_POC.md)

## Fil directeur

Le POC démontre une chaîne technique gouvernée et un résultat négatif mesuré : le fine-tuning apprend le corpus, mais le modèle seul ne sait pas trier ; les garde-fous encadrent la démonstration sans constituer une preuve de sécurité clinique. Chaque chiffre à l’écran provient du rapport et de ses preuves versionnées.

## 1. Assistant IA de triage médical initial

**Notes orales**

Bonjour. Je présente un POC d'assistant de triage initial pour le CHSA. Le système recueille un contexte, propose un des trois niveaux maximum, moderate ou deferred, l'explique et garde une trace d'audit. Il ne diagnostique pas, ne prescrit pas et ne remplace pas le soignant. Tout ce que je montre repose sur des données ouvertes et des scénarios synthétiques.

## 2. Trois questions, pas « un LLM peut-il trier ? »

*Section : 1 · Mission*

**Notes orales**

Le cadrage impose Qwen3-1.7B-Base, un SFT avec LoRA puis un DPO, un endpoint vLLM, une CI/CD et un rapport. Je n'ai pas cherché à répondre à la question : un LLM peut-il remplacer un triage clinique ? La réponse opérationnelle reste non. J'ai évalué trois questions techniques : adapter, aligner, déployer. Et j'ai séparé dès le départ la réussite technique de la réussite clinique.

## 3. Chaque brique a un rôle différent

*Section : 2 · Notions*

**Notes orales**

Un modèle Base continue du texte : il ne sait pas suivre une consigne ni produire du JSON. Le SFT lui montre des paires question-réponse ; LoRA rend cet entraînement abordable en n'entraînant que de petites matrices ajoutées. Le DPO lui apprend à préférer une réponse à une autre. Point clé pour la suite : ces techniques n'ont pas le même rôle. Le fine-tuning apprend un comportement, le RAG apporte de la connaissance, les règles gèrent les signaux critiques.

## 4. Un corpus bilingue traçable… mais sans labels de triage

*Section : 3 · Données*

**Notes orales**

Les quatre sources imposées sont ouvertes, acquises à une révision figée, avec licence et checksum. Un audit du premier corpus a montré que la préparation avait perdu les choix de presque tous les QCM, tronqué des réponses et ne supervisait pas la fin de séquence. J'ai reconstruit plutôt que de viser le chiffre rond de 5 000. Mais retenez la limite : ce sont des questions médicales et des QCM. Il n'y a aucun label de priorité de triage. Cela explique une grande partie des résultats.

## 5. Anonymisation fail-closed, sans certification RGPD

*Section : 3 · Gouvernance*

**Notes orales**

Même avec des sources publiques, j'ai appliqué une chaîne de protection : minimisation, détection Presidio en français et en anglais, remplacement sans table de correspondance, puis rescan. Toute erreur bloque l'admission. Les candidats contextuels comme les noms d'auteurs ou les durées sont conservés sous une décision tracée, pour ne pas détruire le sens médical. Je ne revendique pas une anonymisation RGPD : ce serait une affirmation juridique que ce contrôle technique ne permet pas.

## 6. SFT puis DPO, reproductibles et vérifiés

*Section : 4 · Entraînement*

**Notes orales**

Le SFT repart de la Base exacte, avec LoRA rang 16, 150 étapes et une supervision limitée à la réponse et à son token de fin. J'ai vérifié que l'adaptateur rechargé reproduit exactement 30 générations sur 30. Le DPO part de ce SFT, 20 étapes sur 426 paires. Sa loss baisse et la préférence implicite atteint deux tiers : l'algorithme fait ce qu'on lui demande. Tout est fait sur GPU T4 Kaggle gratuit, avec checksums et versions figées.

## 7. Le SFT apprend nettement le corpus ; le DPO améliore la forme

*Section : 5 · Résultats*

**Notes orales**

Base, SFT et DPO sont rechargés dans le même runtime et évalués sur exactement les mêmes exemples. Le SFT réduit la NLL de 46 % et la répétition de 31 % ; il passe de 0 à 5 réponses exactes sur 30. Le fine-tuning a donc bien appris. Le DPO améliore surtout la forme : plus d'arrêts propres, moins de répétitions, mais aucun gain de contenu. Attention : la NLL mesure la ressemblance avec le corpus, pas la qualité du triage.

## 8. Mais le modèle seul ne sait pas trier

*Section : 5 · Résultats*

**Notes orales**

Voici le résultat central, et il est négatif. Sans contrainte de format, SFT et DPO ne produisent qu'un JSON valide sur 18. Le SFT retenu, testé une seule fois sur la réserve isolée, obtient 0 sur 18, reste bloqué au plafond de longueur et invente des faits patient comme des constantes stables. Ce n'est pas que le fine-tuning ne marche pas : il a appris son objectif. C'est que l'objectif ne correspondait pas à la tâche. Ce résultat est gelé ; je ne l'ai pas utilisé pour retoucher le système.

## 9. Avec garde-fous : sorties valides, mais surtout grâce aux règles

*Section : 6 · Système*

**Notes orales**

Le service ne livre jamais la sortie brute. Il impose un schéma au décodage et applique des garde-fous déterministes. Sur les 18 scénarios, les six cas critiques ressortent bien en maximum. Mais regardez les barres : pour le SFT, 13 sorties sur 18 sont corrigées ou remplacées. La bonne priorité vient majoritairement des règles, pas du modèle. Ce run utilise les adaptateurs antérieurs au corpus final, sur un lot déjà consulté : c'est une preuve d'ingénierie, pas de sécurité clinique.

## 10. Frontend toujours disponible, GPU uniquement à la demande

*Section : 7 · Architecture*

**Notes orales**

Le site statique est sur Cloudflare Pages et reste disponible en permanence. Une Function Cloudflare vérifie le token de démonstration et appelle Modal avec un secret que le navigateur ne voit jamais. Côté Modal, un GPU T4 démarre à la demande et s'éteint après deux minutes d'inactivité. FastAPI valide et anonymise, vLLM génère sous schéma, les garde-fous vérifient, et l'audit est écrit avant toute réponse : s'il échoue, on renvoie une erreur. Le coût de la preuve a été de 5 centimes. En revanche un cold start prend environ deux minutes : c'est une démo, pas un service temps réel.

## 11. Démo : deux scénarios synthétiques

*Section : Démonstration*

**Notes orales**

Je lance la démo. Pendant le réveil du GPU, le frontend affiche l'attente. Premier scénario, douleur thoracique en français : la réponse donne maximum, les signaux d'alerte, l'avertissement et un identifiant d'interaction qu'on retrouve dans l'audit. Deuxième scénario en anglais. Je le dis clairement : dans ces deux cas, c'est le garde-fou qui a remplacé la sortie du modèle. Si la démo ne répond pas à temps, j'ai les captures et la preuve de déploiement.

## 12. Répartir les responsabilités au lieu de tout demander aux poids

*Section : 8 · Stratégie*

**Notes orales**

La leçon principale : on a demandé aux poids d'apprendre en même temps la connaissance, la procédure et la sécurité. Chaque technique est forte sur un besoin différent. L'architecture que je recommande sépare les rôles : des règles déterministes pour les signaux critiques, un RAG hybride pour une connaissance médicale versionnée et citable, un LLM pour comprendre et formuler, des vérificateurs pour la fidélité, et le professionnel qui décide.

## 13. Mesurer avant de réentraîner

*Section : 9 · Recommandations*

**Notes orales**

Ma recommandation est de ne pas dépenser le prochain budget en entraînement. D'abord un jeu d'évaluation de meilleure qualité et un corpus documentaire autorisé. Ensuite une baseline RAG comparée au modèle seul et à un modèle plus capable. Un nouveau SFT ou DPO seulement si un déficit de comportement précis est démontré, avec des données de triage validées par des soignants. Le passage à 32 milliards de paramètres prévu au cadrage reste une hypothèse : il change l'infrastructure et le coût, mais ne corrige pas l'absence de données de triage.

## 14. Ce que le POC démontre, et ce qu'il ne démontre pas

*Section : Conclusion*

**Notes orales**

Pour conclure : le POC atteint ses objectifs techniques et montre des pratiques souvent négligées, comme les checksums, l'isolement des jeux et la publication des résultats négatifs. Il ne démontre pas de capacité de triage du modèle, ni de sécurité clinique. La suite proposée donne à chaque brique sa responsabilité, puis exige une validation clinique indépendante. Merci, je suis prêt pour vos questions.
