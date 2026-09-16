# Pourquoi vérifier les données puis faire un pilote

- Date : 2026-09-11
- Statut : draft
- Sources : ADR-012, preuve SFT_V2_READINESS_2026-09-11, expérience synthétique de reprise CPU.

## Ce que nous avons fait et pourquoi

Le premier SFT avait appris un format de réponse mal terminé et reçu des QCM incomplets. Les micro-runs ont vérifié la correction de ce format ; ils ne suffisaient pas à décider de relancer plusieurs heures.

Nous avons donc vérifié la chaîne entière jusqu'aux labels réellement vus par le trainer. Sur les 4 200 exemples de développement retenus, le texte correspond aux sources (avec les anonymisations expliquées), les choix sont présents, aucun token de réponse n'est tronqué et l'EOS est supervisé. Le prompt sert de contexte : il est lu par le modèle, mais ses tokens ne participent pas directement à la loss.

## Ce que « propre » veut dire ici

Un corpus peut ne contenir aucune question identique et néanmoins exposer le même document dans train et validation. C'est comparable à réviser un chapitre puis être évalué sur une autre phrase de ce même chapitre : le test mesure moins bien la généralisation à un document nouveau.

Nous avons retiré 297 lignes qui recoupaient un groupe réservé à l'évaluation, puis 3 QCM dont les choix se répétaient dans la source. Aucun exemple de test n'a été déplacé vers train. Le corpus final de préparation contient 4 700 lignes. La petite réduction d'effectif est préférable à des quotas remplis avec des ambiguïtés connues.

« Propre techniquement » ne signifie pas « vérité médicale certifiée ». Une référence source peut être datée ou discutable. Le scan des identifiants directs ne prouve pas une anonymisation exhaustive ; les noms de maladies et médicaments ne doivent pas être supprimés aveuglément par un détecteur de personnes.

## Pourquoi sauvegarder plus que les poids

Les poids sont le résultat acquis. L'optimiseur conserve une mémoire des mises à jour ; le scheduler indique où l'on se trouve dans le calendrier du taux d'apprentissage ; les RNG et l'état du trainer permettent de retrouver l'ordre et le point de reprise.

Nous avons testé un modèle miniature sur des textes synthétiques : quatre étapes continues donnent exactement les mêmes poids que deux étapes, une interruption et deux étapes reprises. Cette preuve CPU ne remplace pas le contrôle sur CUDA avec la quantification et le scaler de précision mixte.

## Ce que fera le pilote

Il repartira de la base, avec les données corrigées, et s'arrêtera à 150 étapes ou au budget de 30 minutes de la phase d'entraînement. La préparation et l'évaluation prennent du temps en plus. Les premières étapes parcourent une partie du jeu train complet figé ; ce n'est pas un entraînement complet de quatre heures.

La validation est fixée avant de voir les nouvelles sorties. Nous comparerons les réponses de la base et du pilote, leur terminaison, leurs répétitions, la concordance aux références et la loss sur les réponses. Une baisse de loss seule ne suffira pas. Si les preuves sont encourageantes et la reprise GPU vérifiée, nous pourrons poursuivre depuis le checkpoint ; sinon, nous analyserons les erreurs avant toute dépense supplémentaire.

Aucun nouveau SFT médical n'a été lancé lors de cette vérification. La préparation et les limites sont présentées à l'utilisateur avant le lancement, conformément à sa demande.
