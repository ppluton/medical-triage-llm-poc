# Validation locale de la chaîne post-SFT

- **Date :** 2026-09-05
- **Statut :** draft
- **Sources :** code et tests de `codex/complete-poc-evaluation`, parent `2a40562`, ADR-010, artefacts locaux DPO.

## Question et environnement

Peut-on comparer les checkpoints sur les mêmes entrées, empêcher un DPO sans revue et recevoir une réponse structurée d'un fournisseur compatible vLLM sans journaliser le texte médical ?

Validation sur macOS, Python 3.13, environnement local existant ; les transports HTTP du fournisseur sont simulés. Commandes depuis le worktree :

```bash
PYTHONPATH=src /Users/ppluton/Documents/ChatGPT/Medical_train_llm/.venv/bin/python -m pytest -q
/Users/ppluton/Documents/ChatGPT/Medical_train_llm/.venv/bin/ruff check src scripts tests
```

## Résultats observés

- Dernière exécution complète : 88 tests réussis, 8,48 s ; avertissements Starlette/httpx et cache pytest non inscriptible dans le sandbox.
- Ruff sans cache : aucun défaut.
- Ruff : aucun défaut après correction des imports.
- Contrats comparatifs : mêmes identifiants et tokens, agrégation pondérée, sélection déterministe, refus de troncature.
- DPO : refus de comparaison non terminée, de décision non liée au checksum, de données non approuvées, de fuite de prompts et de scan direct sans revue complémentaire.
- API : schéma, anonymisation avant transport simulé, réponses tronquées/invalides refusées, audit sans texte, refus lorsque l'audit échoue.
- Détection email : test interdisant tout appel `requests`, suffixes embarqués, pas de cache writable.

Ces résultats prouvent les comportements testés localement. Ils ne prouvent pas une inférence vLLM réelle, un gain médical, une latence cible, une revue clinique ou un déploiement.

## Conteneur

L'image intermédiaire a été construite et testée avec `docker run --rm --network none` : `/healthz` retourne 200 ; `/v1/triage` sans fournisseur retourne 503 ; un email synthétique est masqué par les vrais modèles Presidio/spaCy. Ce premier test a révélé des tentatives de téléchargement de la liste de suffixes publics. Le code a été corrigé avec `OfflineEmailRecognizer` ; la reconstruction a réussi. L’image corrigée `sha256:27298625e0ad154aec9fa46236dacdaf17ebbce7fc65c16ed1fb546c38c9c213` a passé les mêmes assertions avec toute requête `requests` interdite par une assertion, sous `--network none`. Aucun téléchargement n’a été tenté.

## Candidats DPO

Artefacts privés locaux : `artifacts/dpo-candidates-v1` (rejeté) et `artifacts/dpo-candidates-v2` (candidat). Aucun entraînement DPO n'est prouvé ici.

Le premier lot de 512 + 64 paires a été rejeté : NER masquait notamment des notions biomédicales comme des personnes ou des lieux. Il n'a pas été utilisé pour entraîner.

Le second lot emploie la politique d'identifiants directs déjà utilisée pour le SFT source. Les checksums source/index sont vérifiés ; les prompts SFT et réservés au test sont exclus par empreintes normalisées. Trois prompts protégés/doublons et un texte hors plafond ont été écartés.

| Split | Paires | Prompt max. | Séquence max. | Au-delà de 2 048 tokens |
|---|---:|---:|---:|---:|
| train | 512 | 655 | 1 639 | 0 |
| validation | 64 | 450 | 1 116 | 0 |

Types source : train `length=206`, `easy=105`, `hard=201` ; validation `length=29`, `easy=10`, `hard=25`. Un seul masque `PHONE_NUMBER`, dans une pagination bibliographique, reste présent. La revue de cet exemple montre un faux positif ; il doit être exclu ou corrigé avec traçabilité lors de la revue. Aucun statut d'approbation n'est attribué au lot.

Limites : candidats uniquement anglais, sélection dans l'ordre source, pas de décontamination sémantique, pas de revue clinique des préférences ni de revue exhaustive de confidentialité. Les références du test ne servent pas à sélectionner les préférences.

## Étape suivante

Terminer et archiver la comparaison Kaggle Base/SFT, revoir les générations puis décider du périmètre DPO. Le test final et la démonstration avec inférence réelle restent distincts.
