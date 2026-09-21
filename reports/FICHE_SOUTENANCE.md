# Fiche de soutenance — POC LLM de triage médical

- Date : 2026-09-16
- Statut : `final_candidate`
- Usage : aide-mémoire personnel pour la présentation et les questions du jury
- Sources : `reports/PRESENTATION_POC.md`, `reports/RAPPORT_TECHNIQUE_POC.md`, preuves versionnées et [consignes de soutenance OpenClassrooms](https://openclassrooms.com/fr/paths/2053/projects/3421/8586-livrables-et-soutenance)

## Pitch en 30 secondes

J’ai construit un POC bilingue de triage initial autour de Qwen3-1.7B. J’ai préparé et anonymisé un corpus médical, entraîné un SFT avec LoRA, testé un alignement DPO, puis comparé les variantes sur des jeux isolés. Le modèle brut échoue encore au contrat de triage. Je l’ai donc intégré derrière FastAPI, vLLM, un schéma contraint, des garde-fous et un audit. Le frontend Cloudflare appelle une API GPU Modal protégée et scale-to-zero. Le projet démontre une faisabilité technique, pas une validation clinique.

## Le projet en une phrase

Une chaîne auditable allant de données médicales ouvertes à un démonstrateur cloud bilingue, avec un modèle expérimental encadré par des contrôles déterministes et une décision humaine obligatoire.

## Déroulé conseillé

| Temps | Sujet | Message à faire retenir |
|---:|---|---|
| 0:00–1:00 | Mission | Assistant pédagogique, aucune décision clinique autonome |
| 1:00–3:00 | Données | Qualité, séparation des splits, anonymisation et traçabilité |
| 3:00–5:30 | SFT et LoRA | Le modèle apprend mieux le corpus à coût GPU réduit |
| 5:30–7:00 | DPO | L’optimisation fonctionne, mais le bénéfice n’est pas assez robuste |
| 7:00–8:30 | Réserve finale | Le résultat négatif impose des garde-fous |
| 8:30–10:30 | Architecture | Cloudflare, Modal, FastAPI, vLLM, audit et secrets |
| 10:30–12:00 | CI/CD et limites | Reproductibilité prouvée, pertinence clinique non prouvée |
| 12:00–15:00 | Démonstration | Parcours synthétique public et interprétation encadrée |

## Glossaire à expliquer simplement

Ces définitions permettent de vulgariser chaque brique sans perdre la distinction entre performance du modèle et sûreté du système.

### LLM

Un modèle de langage prédit le prochain token à partir du contexte. Il peut produire une réponse fluide sans que cette réponse soit factuellement correcte.

### Base model

Qwen3-1.7B-Base est le modèle avant adaptation au corpus du projet. Il sert de référence pour mesurer l’effet du SFT et du DPO.

### SFT

Le **Supervised Fine-Tuning** montre au modèle des paires instruction-réponse attendues. Le modèle ajuste ses paramètres afin de donner davantage de probabilité à ces réponses. La loss mesure cet écart probabiliste ; elle ne mesure pas directement la qualité clinique.

### LoRA

La **Low-Rank Adaptation** ajoute de petits modules entraînables au modèle. Les poids principaux restent gelés. Cela réduit la mémoire GPU, accélère l’entraînement et produit un adaptateur plus facile à stocker qu’un modèle complet.

### DPO

La **Direct Preference Optimization** part de paires `chosen` et `rejected`. Après le SFT, elle pousse le modèle à préférer la réponse choisie. Dans ce projet, le DPO est exécuté correctement mais reste court et ses préférences ne sont pas des annotations cliniques de triage.

### NLL ou loss

La Negative Log-Likelihood mesure la surprise du modèle face aux tokens de référence. Plus elle baisse, mieux le modèle reproduit ce type de texte. Une NLL de 0,83 ne signifie pas 83 % de précision.

### EOS

Le token End Of Sequence indique que le modèle a terminé sa réponse. Une génération terminée n’est pas nécessairement correcte.

### vLLM

vLLM est le moteur d’inférence GPU. Il optimise le chargement et la génération du modèle. FastAPI gère le contrat HTTP autour de lui.

### Garde-fou déterministe

Une règle de code vérifiable qui impose un plancher de priorité, rejette une sortie malformée ou remplace une réponse risquée par un fallback conservateur. Contrairement au modèle, son comportement est explicitement testé.

### Scale-to-zero

Modal arrête les tâches GPU après une période d’inactivité. Le coût diminue, mais le premier appel suivant subit un cold start.

## Les chiffres à connaître

| Sujet | Chiffre | Interprétation correcte |
|---|---:|---|
| Corpus final | 4 700 | Cible proche de 5 000, qualité privilégiée |
| Train / validation / test | 3 721 / 479 / 500 | Splits séparés |
| Langues | 2 474 FR / 2 226 EN | Bilingue en nombre de lignes, pas forcément en tokens |
| SFT v39 | 150 étapes | Adaptateur final lié au corpus v2.2 |
| DPO v41 | 20 étapes | Expérience bornée, 426 paires train et 54 validation |
| Recharge SFT | 30/30 identiques | Reproductibilité du checkpoint |
| Réserve finale | 0/18 JSON conforme | Le modèle brut ne respecte pas le contrat |
| CI finale | 252 tests | Preuve logicielle, pas clinique |
| Public | 2 scénarios audités | Smoke test réel, pas benchmark |
| Cold start | 111 et 117,5 s observés | Conséquence du scale-to-zero |
| Appels chauds | environ 30 à 35 s | Mesures sur deux scénarios seulement |

## Pourquoi le DPO n’a-t-il pas été retenu ?

Le DPO améliore légèrement la NLL, l’arrêt EOS et la répétition. Il n’améliore pas le nombre de réponses exactes. La revue aveugle trouve aussi un signal diagnostic ou prescriptif supplémentaire. La règle fixée avant la réserve exigeait une amélioration sans régression suivie. Le DPO ne dominait donc pas le SFT.

Réponse courte au jury : « L’entraînement DPO a fonctionné techniquement, mais les preuves ne justifiaient pas de déployer cet adaptateur. J’ai privilégié la sélection fondée sur les résultats plutôt que le simple fait d’avoir entraîné un modèle supplémentaire. »

## Pourquoi déployer un modèle qui échoue à 0/18 en brut ?

La réserve mesure volontairement le composant modèle sans le système de garde. Elle montre précisément pourquoi le modèle ne peut pas être utilisé seul. Le POC déployé évalue l’architecture complète : décodage contraint, validation du schéma, fallback, garde-fous, audit et décision humaine.

Réponse courte au jury : « Le résultat négatif n’est pas caché. Il devient une exigence d’architecture et une limite explicite du POC. »

## Architecture à raconter

1. Le navigateur charge un frontend statique depuis Cloudflare Pages.
2. L’utilisateur fournit un token de démonstration.
3. Une Cloudflare Function vérifie ce token et protège l’URL Modal.
4. Modal démarre un GPU T4 si nécessaire.
5. FastAPI valide et anonymise le contexte.
6. vLLM exécute Qwen3 avec l’adaptateur SFT sélectionné.
7. Les garde-fous bornent la priorité et peuvent appliquer un fallback sûr.
8. L’API renvoie l’avertissement et un identifiant d’interaction.
9. L’audit privé conserve versions, décisions et durée, sans journaliser les secrets.

## Déroulé de démonstration

La démonstration doit rester courte, reproductible et limitée aux scénarios synthétiques fournis. Elle porte sur une chaîne gouvernée (API, garde-fous, erreurs, traçabilité, décision humaine) et non sur une autonomie du modèle.

### Conditions

- Modèle : SFT v39 retenu avant ouverture de la réserve ; consigner son empreinte, le prompt, la version du serveur et le code.
- Données : exclusivement des scénarios synthétiques de démonstration, distincts de la réserve finale figée.
- Cible : le serveur cloud, son accès privé et son coût doivent avoir une cible autorisée. Un appel au fournisseur simulé n’est pas une démonstration du modèle.
- Frontend public : [triage-poc.pierrepluton.com](https://triage-poc.pierrepluton.com/). Le proxy refuse les mauvais tokens et transmet les appels autorisés à l’endpoint GPU Modal. Le contrat `/docs` complète la preuve d’intégrabilité, sans remplacer le parcours réel.
- Mesure hors démonstration : `scripts/evaluate_triage_endpoint.py`, puis rapprochement avec `scripts/verify_endpoint_audit.py`. Le token passe par `TRIAGE_API_TOKEN`, jamais dans une diapositive ou une commande publiée. Les rapports bruts restent hors Git.

### Préparation

Récupérer le token de démonstration depuis le gestionnaire de secrets et le copier dans le presse-papiers sans l’afficher. Le token est saisi au début de la session ; il n’est ni conservé par le navigateur ni montré au public.

### Scénario conseillé

Dans l’interface `/demo`, utiliser « Douleur thoracique » en français, puis basculer sur le scénario neurologique anglais. Montrer :

- les informations structurées et l’étiquette synthétique ;
- le token collé sans être affiché ailleurs ;
- le statut de réveil du modèle ;
- la priorité `maximum` et les informations manquantes ;
- les signaux d’alerte ;
- l’avertissement de non-diagnostic ;
- la latence et l’identifiant d’interaction qui permet le rapprochement d’audit.

### État établi avant la démonstration

- SFT v39 et DPO v41 terminés, rechargeables et vérifiés. Sur le développement v43, NLL Base/SFT/DPO = 1,532/0,830/0,829 ; le DPO ajoute un signal diagnostic ou prescriptif en revue aveugle et n’est pas retenu.
- Réserve v46, ouverte une seule fois : 0/18 JSON conforme, 17/18 sorties au plafond, 18/18 malformées ou répétitives. Aucun réglage ni réentraînement n’a suivi.
- API v34 : 18/18 réponses conformes grâce au schéma contraint et aux garde-fous, 8/18 priorités égales aux références pédagogiques proposées ; niveau intermédiaire non utilisé, cas incomplets faibles. La v37 confirme l’exécution Base/SFT/DPO et deux dialogues FR/EN.
- Démonstration publique vérifiée sur deux cas synthétiques (douleur thoracique FR, déficit neurologique EN) : `maximum`, fallback sûr v3, interactions retrouvées dans l’audit privé. Cette preuve ne couvre ni la charge, ni la disponibilité continue, ni une validation clinique.

### Explication orale des résultats

« Le SFT apprend à mieux reproduire les réponses du corpus. Le DPO apprend à préférer certaines réponses aux autres. Nous avons exécuté les deux étapes, puis comparé les trois modèles sur les mêmes exemples de développement. Le DPO améliore certaines métriques de forme, mais pas assez pour compenser une régression qualitative ; nous avons donc retenu le SFT avant d’ouvrir la réserve. Sur cette réserve, le modèle brut échoue au contrat de triage. Nous ne le présentons pas comme prêt à trier des patients. La démonstration porte sur la chaîne API, ses garde-fous, ses erreurs, sa traçabilité et la décision humaine. »

Un JSON valide ne prouve pas une bonne priorité : vérifier aussi les informations inventées et les questions posées. Les priorités de référence des scénarios restent proposées, sans validation clinique.

### Si Modal est froid

Expliquer : « Le GPU est volontairement arrêté quand personne n’utilise le POC. Le réveil peut prendre environ deux minutes et protège le budget. » Ne pas remplir le silence : poursuivre les explications d’architecture pendant le démarrage.

### Si la démonstration échoue

Ne pas improviser un diagnostic. Montrer l’erreur et le journal technique expurgé, puis la preuve de déploiement, et dire exactement : « Le chemin public a déjà été vérifié sur deux scénarios synthétiques et rapproché de l’audit. L’échec actuel concerne la disponibilité de démonstration, pas une nouvelle preuve clinique. » Ne pas remplacer silencieusement la réponse par une sortie préécrite ou par un autre modèle ; une capture d’une exécution antérieure doit porter sa version et être présentée comme telle.

## Questions probables du jury

Les réponses suivantes préparent les thèmes explicitement annoncés par OpenClassrooms : méthodologie, fine-tuning, optimisation, passage à l’échelle et déploiement.

### Pourquoi Qwen3-1.7B ?

Le modèle reste assez petit pour un entraînement et une inférence accessibles sur GPU étudiant. La révision exacte est figée, sa licence est consignée et les poids sont vérifiés par checksum.

### Pourquoi environ 5 000 exemples et pas davantage ?

La mission cible environ 5 000 paires. L’audit a conduit à retenir 4 700 exemples de meilleure qualité. Ajouter des lignes défectueuses aurait artificiellement atteint la cible sans améliorer le corpus.

### Le corpus est-il vraiment anonymisé ?

Le pipeline masque les identifiants directs détectés et le rescan technique n’en trouve plus. Je ne revendique pas une anonymisation exhaustive ou une conformité RGPD certifiée. Une vraie mise en œuvre demanderait une DPIA, une base légale et une revue du DPO.

### Pourquoi le frontend est-il sur Cloudflare et le modèle sur Modal ?

Cloudflare héberge très bien le statique et le proxy d’accès, mais pas ce modèle GPU avec vLLM. Modal fournit le GPU à la demande. La séparation réduit le coût et évite d’exposer directement l’API Modal.

### Pourquoi pas Azure, Railway ou Hugging Face Spaces ?

Les contraintes de régions et de quota ont bloqué Azure pour ce compte. Railway et Cloudflare ne fournissaient pas ici un GPU gratuit adapté à vLLM. Modal offrait un crédit borné et un scale-to-zero compatible avec une soutenance ponctuelle.

### Le système est-il sécurisé ?

Pour un POC : secrets fournisseur, Bearer token, HTTPS, CSP, absence de secret dans Git, journalisation minimisée et rejet des méthodes non prévues. Pour un usage réel, il manquerait identité nominative, rotation automatisée, WAF/rate limiting documenté, DPIA, supervision et procédures d’incident.

### Quelle est la valeur ajoutée clinique ?

La valeur potentielle tient à une collecte plus structurée, une escalade conservatrice en présence d’un signal d’alerte et une trace auditable. Le POC ne démontre pas encore que ces éléments améliorent un résultat de santé ou le travail d’un service réel. Cette valeur doit être évaluée avec des professionnels sur un protocole clinique indépendant.

### Comment passer à l’échelle ?

Le POC limite volontairement Modal à un conteneur pour contrôler le coût. Une montée en charge demanderait des tests de concurrence, un dimensionnement GPU, une politique d’autoscaling, des quotas, du rate limiting, des métriques de saturation et un budget. La sécurité clinique et la supervision doivent être validées avant d’augmenter le trafic.

### Peut-on conclure que le SFT est meilleur ?

Oui pour la reproduction du corpus dans le protocole mesuré. Non pour la pertinence clinique du triage. Les deux conclusions doivent rester séparées.

### Pourquoi conserver les résultats négatifs ?

Ils évitent de présenter une fausse réussite, expliquent les garde-fous et rendent les itérations auditables. La traçabilité est un livrable du projet.

## Formulations à employer

- « POC pédagogique »
- « priorité proposée »
- « scénario synthétique »
- « garde-fou proposé et déterministe »
- « résultat technique observé »
- « non validé cliniquement »
- « décision humaine obligatoire »

## Formulations à éviter

- « diagnostic »
- « précision clinique »
- « validé RGPD »
- « prêt pour l’hôpital »
- « le modèle comprend le patient »
- « 83 % de précision » pour une loss à 0,83
- « le DPO est meilleur » sans rappeler la décision de sélection

## Checklist le jour J

- Batterie, réseau et partage d’écran vérifiés.
- PowerPoint ouvert en mode présentateur (notes orales incluses), PDF de secours à côté.
- Frontend public ouvert dans un onglet séparé.
- Token récupéré depuis le gestionnaire de secrets et copié sans affichage.
- Modal réveillé cinq minutes avant la démonstration si le budget le permet.
- Preuves v43, v46, Modal et Cloudflare ouvertes en secours.
- Chronomètre : 12 minutes de slides, 3 minutes de démonstration.
- Aucun vrai renseignement patient saisi ou affiché.
