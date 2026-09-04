# Utiliser Kaggle pour le SFT complet

- **Date :** 2026-09-04
- **Statut :** observed
- **Sources :** interface Kaggle du projet, configuration SFT source-derived, documentation technique du dépôt

## Ce qui a été fait

Le SFT complet de Qwen3-1.7B Base a été lancé dans un notebook Kaggle privé après un micro-run CUDA obligatoire. Le MacBook Air reste l'environnement de préparation, de contrôle et de documentation ; Kaggle fournit temporairement le GPU nécessaire à l'entraînement.

Le dataset Kaggle est lui aussi privé. Il contient les 4 000 lignes `train`, les 500 lignes `validation`, les scripts et la configuration nécessaires, mais aucune ligne du split `test`. Les sorties d'entraînement sont écrites dans `/kaggle/working` et doivent être téléchargées avant d'être considérées comme archivées durablement.

## Comment fonctionne un notebook Kaggle

Un notebook Kaggle associe quatre éléments :

1. un document exécutable composé de cellules de texte et de code ;
2. une machine distante temporaire, avec CPU ou GPU selon les réglages ;
3. des datasets montés en lecture seule sous `/kaggle/input` ;
4. un espace de travail écrivable sous `/kaggle/working` pour les résultats du run.

Lancer **Save Version** crée une version immuable du notebook et peut exécuter toutes les cellules sur les serveurs Kaggle. Le navigateur et le Mac peuvent ensuite être fermés : le calcul continue côté Kaggle. Pendant l'exécution, **Active Events**, puis **Logs**, affiche le statut et la progression. Quand la version termine, les fichiers conservés dans `/kaggle/working` apparaissent dans **Output**.

## Parcours utilisé pour ce projet

1. Ouvrir le notebook privé `CHSA Source SFT Qwen3`.
2. Vérifier que le dataset privé `chsa-source-sft-v1` est attaché.
3. Vérifier l'accélérateur GPU et l'accès Internet nécessaire au téléchargement du modèle et des dépendances.
4. Lancer une nouvelle version avec le micro-run et le run complet activés.
5. Suivre **Active Events > Version en cours > Logs**.
6. Attendre un statut final `Complete` ou `Successful` avant d'utiliser les sorties.
7. Télécharger et vérifier les résumés, adaptateurs et checksums utiles.
8. Versionner dans `docs/evidence/` les mesures observées et leurs limites, sans versionner les poids volumineux.

## Kaggle par rapport au MacBook Air

| Sujet | MacBook Air local | Kaggle |
|---|---|---|
| Calcul | Apple Silicon avec MLX | GPU NVIDIA CUDA temporaire |
| Disponibilité | contrôlée par le propriétaire | soumise aux quotas et à la disponibilité Kaggle |
| Données | restent sur le stockage local | sont téléversées dans un dataset Kaggle |
| Persistance | fichiers conservés tant qu'ils ne sont pas supprimés | machine éphémère ; sorties à sauvegarder explicitement |
| Reproductibilité | dépend de l'environnement local | version de notebook et logs conservés par run |
| Coût immédiat | matériel déjà possédé | quota GPU gratuit, sans garantie de capacité future |
| Simplicité | installation et dépendances à maintenir | environnement prêt à l'emploi, mais interface et stockage distincts |

## Avantages retenus

- le GPU CUDA réduit fortement la durée attendue par rapport au micro-run MLX local ;
- le Mac reste disponible pendant l'entraînement ;
- le notebook versionné par Kaggle conserve les cellules et les logs d'une exécution ;
- le quota gratuit suffit à cette expérimentation tant que le run reste borné ;
- le micro-run puis le run complet peuvent partager le même environnement distant.

## Inconvénients et précautions

- les quotas, accélérateurs et durées maximales peuvent changer ;
- l'environnement est éphémère et les sorties non téléchargées peuvent être perdues ;
- un dataset privé n'autorise pas l'envoi de données patient ou de secrets ;
- l'interface peut afficher une ancienne version dans l'onglet principal pendant qu'une nouvelle version tourne dans **Active Events** ;
- une allocation `GPU T4 x2` ne signifie pas que le code exploite automatiquement deux GPU ; le run actuel utilise volontairement un seul T4 ;
- les sorties Kaggle et locales ne sont comparables que si le modèle, les données, la seed et les hyperparamètres sont consignés.

## Ce que ce choix ne prouve pas

Kaggle apporte une capacité de calcul, pas une validation clinique. La fin du SFT ne prouvera ni une amélioration par rapport au modèle Base, ni une capacité fiable de triage. Ces questions seront traitées séparément par la comparaison Base/SFT, le DPO, l'évaluation de sûreté et une éventuelle revue clinique.

## Étape suivante

Après la fin du run, télécharger les sorties, vérifier leur intégrité, documenter les métriques observées dans `docs/evidence/`, puis exécuter la comparaison Base versus SFT sur le même protocole isolé.
