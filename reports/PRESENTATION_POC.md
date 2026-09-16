# Présentation du POC d’assistance au triage médical CHSA

- Date : 2026-09-16
- Statut : `final_candidate`
- Format : 12 diapositives, 16:9, 12 minutes de présentation et 3 minutes de démonstration
- Support local : `output/pptx/poc-triage-medical-chsa-v47.pptx`
- Sources : documents de cadrage, manifestes v2.2, résultats SFT v39, DPO v41, sélection v43, réserve v46, déploiements Modal et Cloudflare, CI de la PR #4 et [consignes de soutenance OpenClassrooms](https://openclassrooms.com/fr/paths/2053/projects/3421/8586-livrables-et-soutenance)

## Fil directeur

Le projet ne cherche pas à présenter un modèle comme médecin autonome. Il démontre une chaîne technique gouvernée : données traçables, adaptation mesurée, résultat final négatif assumé, garde-fous explicites, endpoint cloud protégé et audit. Chaque affirmation de la soutenance correspond à une preuve versionnée.

## 1. POC d’assistance au triage médical

**À l’écran**

- Qwen3-1.7B, SFT LoRA, DPO, FastAPI, vLLM
- Démonstrateur pédagogique CHSA
- Décision humaine obligatoire

**Notes orales**

Le POC recueille un contexte synthétique en français ou en anglais, propose un niveau de priorité encadré et conserve une trace d’audit. Il ne diagnostique pas, ne prescrit pas et ne remplace aucun professionnel. La présentation distingue ce que le modèle apprend, ce que le système sécurise et ce qui reste non validé.

## 2. Mission et périmètre

**À l’écran**

- Entrée : contexte symptomatique synthétique FR ou EN
- Sorties : `maximum`, `moderate`, `deferred`
- Avertissement et identifiant d’interaction
- Aucun diagnostic ou usage sur de vrais patients
- Valeur potentielle : collecte structurée, escalade conservatrice et traçabilité

**Notes orales**

L’objectif scolaire est une faisabilité technique de triage initial. L’API limite volontairement les sorties à trois valeurs. Sa valeur clinique potentielle réside dans une collecte plus structurée, une escalade prudente et une trace exploitable. Ces bénéfices restent des hypothèses à confirmer par une validation clinique indépendante.

## 3. Chaîne de réalisation

**À l’écran**

Sources ouvertes, gouvernance, corpus v2.2, SFT, DPO, comparaison, réserve, API et audit.

**Notes orales**

Le projet commence par les sources et leurs licences. Le pipeline nettoie et anonymise les données avant le SFT. Le DPO intervient ensuite sur des préférences séparées. Base, SFT et DPO sont comparés sur le même protocole de développement. Une réserve isolée sert au résultat final. Le modèle retenu est ensuite placé derrière FastAPI, vLLM et des garde-fous.

## 4. Corpus v2.2 et gouvernance

**À l’écran**

- 4 700 exemples bilingues
- 3 721 train, 479 validation, 500 test
- 2 474 FR et 2 226 EN
- 31 occurrences de noms masquées sur 22 lignes

**Notes orales**

Le premier corpus de 5 000 lignes contenait un défaut de transformation : 2 249 QCM sur 2 250 avaient perdu leurs choix. La correction privilégie la qualité et conduit à 4 700 exemples. Le rescan technique ne trouve plus d’identifiant direct, mais cela ne vaut ni certification RGPD ni anonymisation exhaustive.

## 5. SFT avec LoRA

**À l’écran**

- Qwen3-1.7B-Base, révision figée
- Adaptateur LoRA, 150 étapes, seed 42
- NLL validation : 1,4569 vers 0,7118 pendant le run
- Recharge : 30 générations sur 30 identiques

**Notes orales**

Le SFT montre au modèle les réponses attendues. LoRA entraîne de petits adaptateurs au lieu de modifier tous les poids, ce qui réduit l’empreinte GPU. La baisse de loss signifie que le modèle apprend mieux le corpus. Elle ne signifie pas 71 % de bonnes réponses et ne prouve aucune pertinence clinique. La recharge identique démontre la reproductibilité du checkpoint.

## 6. DPO et décision de sélection

**À l’écran**

- 426 paires train, 54 validation
- 20 étapes ; 392 tenseurs de politique modifiés
- Meilleure terminaison et moins de répétition
- SFT retenu à cause d’une régression qualitative DPO

**Notes orales**

Le DPO apprend à préférer une réponse choisie à une réponse rejetée. L’expérience a bien exécuté l’optimisation, mais elle reste courte et les préférences ne sont pas des décisions de triage validées. Le DPO améliore plusieurs métriques de forme sans améliorer le nombre de réponses exactes. La revue aveugle signale un cas diagnostic ou prescriptif supplémentaire. La règle de sélection retient donc le SFT v39.

## 7. Réserve finale et conséquence de sûreté

**À l’écran**

- 0 JSON conforme sur 18 scénarios
- 17 sorties sur 18 au plafond de tokens
- 18 sorties signalées
- Au moins 6 faits patient inventés

**Notes orales**

La réserve finale a été ouverte une seule fois après la sélection. Le modèle brut échoue au contrat de triage. Il répète, produit du texte malformé et invente des informations patient. Ce résultat négatif est essentiel : il montre que l’adaptateur seul ne peut pas constituer le produit. Le schéma contraint et les garde-fous deviennent des composants nécessaires du POC.

## 8. Architecture cloud déployée

**À l’écran**

Navigateur, Cloudflare Pages, Function proxy, Modal T4, FastAPI, vLLM, garde-fous et audit.

**Notes orales**

Le frontend statique est hébergé sur Cloudflare Pages. Une Function contrôle le Bearer token et relaie la requête avec un token serveur. Modal démarre un GPU T4 à la demande, charge Qwen3 et l’adaptateur SFT, puis expose FastAPI et vLLM. Le service revient à zéro tâche après 120 secondes d’inactivité afin de préserver les crédits.

## 9. Preuve publique et protection

**À l’écran**

- Domaine HTTPS actif
- Rejet 401 avec mauvais token et 405 avec mauvaise méthode
- Deux scénarios synthétiques FR/EN exercés de bout en bout
- `maximum`, fallback sûr et audit rapproché pour les deux

**Notes orales**

Le chemin public a été testé avec une douleur thoracique en français et un déficit neurologique en anglais. Les réponses ont été rapprochées du journal privé grâce à leurs identifiants. Les latences chaudes observées étaient environ 35 et 30 secondes. Deux cold starts ont pris 111 et 117,5 secondes. Cela prouve le raccord public sur deux cas, pas un benchmark en charge.

## 10. CI/CD et reproductibilité

**À l’écran**

- 252 tests CI et Ruff
- Build Docker et smoke du conteneur
- Workflows Modal et Cloudflare à déclenchement manuel protégé
- Versions, checksums, seeds, logs et décisions conservés

**Notes orales**

La PR exécute les tests, le lint, la validation des manifestes et le build Docker. Les workflows de déploiement demandent une confirmation explicite pour éviter une publication ou une dépense GPU involontaire. Les poids lourds restent privés, mais leurs versions et empreintes sont consignées dans Git.

## 11. Niveau de preuve et feuille de route

**À l’écran**

- Prouvé : pipeline, entraînements, sélection, API cloud et audit sur deux cas
- Partiel : robustesse et latence en conditions limitées
- Non prouvé : pertinence clinique, charge, usage patient et conformité hospitalière
- Suite : validation clinique, tests élargis, monitoring et procédure d’arrêt

**Notes orales**

Le POC satisfait l’attendu de démonstration technique et de reproductibilité. Il ne satisfait pas les conditions d’un usage réel. Une étape clinique indépendante doit valider les scénarios, les seuils et les risques. Un pilote hospitalier demanderait aussi une DPIA, une politique de conservation, une supervision et des procédures opérationnelles.

## 12. Conclusion et démonstration

**À l’écran**

- Le SFT apprend le corpus et se recharge
- Le DPO a été exécuté mais n’a pas été retenu
- Le modèle brut échoue au triage final
- Le système gouverné est déployé et auditable

**Notes orales**

Le résultat du projet tient dans cette distinction : l’entraînement améliore le composant modèle, tandis que l’architecture rend sa démonstration contrôlable. Je termine avec un scénario synthétique dans le frontend public. Si le GPU est froid, j’explique le scale-to-zero et j’utilise la preuve capturée plutôt que de dépasser le temps de soutenance.

## Démonstration en trois minutes

1. Ouvrir `https://triage-poc.pierrepluton.com/`.
2. Coller le token de démonstration sans l’afficher à l’écran.
3. Choisir le scénario synthétique « Douleur thoracique ».
4. Montrer les informations structurées puis lancer l’évaluation.
5. Commenter la priorité, les signaux d’alerte, l’avertissement et l’identifiant d’interaction.
6. Rappeler que le fallback déterministe protège la démonstration lorsque le texte brut du modèle n’est pas fiable.

## Contrôles avant soutenance

- Réveiller Modal cinq minutes avant le passage si une démonstration immédiate est nécessaire.
- Vérifier que le token est dans le presse-papiers, jamais visible dans les slides ou le terminal projeté.
- Garder la preuve de déploiement ouverte comme solution de secours.
- Utiliser uniquement les scénarios synthétiques fournis.
- Ne jamais employer les expressions « validé cliniquement », « diagnostic » ou « prêt pour l’hôpital ».
