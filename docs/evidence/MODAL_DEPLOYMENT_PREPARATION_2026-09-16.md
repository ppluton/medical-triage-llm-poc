# Préparation locale du déploiement Modal

- Date : 2026-09-16
- Statut : `verified_local_definition_not_deployed`
- SDK vérifié : `modal==1.5.5`
- Cible déclarée : T4, zéro conteneur minimum, un conteneur maximum
- Statut clinique : `not_performed`

## Vérifications observées

- import local de `deploy.modal_app` réussi avec le SDK Modal épinglé ;
- définition `chsa-triage-poc` et classe `TriageService` construites sans authentification Modal, avec authentification Bearer applicative obligatoire ;
- cinq fichiers réels du SFT v39 rehashés avec succès, dont l'adaptateur
  `c911f9c631be825f4af5c7dff5a87409d1ee91d4c28e2b0b1571e808e055d413` ;
- dossier privé local de transfert préparé : onze fichiers Base et six fichiers SFT ;
  manifeste Base `920a5897…f0d1` et vérification combinée réussis ;
- manifeste `data/manifests/modal-deployment-assets-v1.json` créé sans chemin local ni secret ;
- le poids Base du dossier de transfert et celui du cache partagent le même inode :
  la préparation n'a pas créé une seconde copie physique de 3,2 Gio ;
- dix-huit tests ciblés `test_modal_deployment.py` et `test_serving.py` réussis ;
- Ruff réussi sur le module de déploiement, la factory de service et leurs tests ;
- le workflow GitHub est manuel et référence un environnement protégé `modal-demo`.
- régression complète finale `val_d3cacf40d752` : 240 tests réussis, deux avertissements de
  dépréciation externes connus ; Ruff réussi sur `src`, `scripts`, `tests` et `deploy`.
- contrôle Modal non mutant après le commit : `modal token info` indique `Token missing` ;
  aucun profil authentifié n'est actuellement disponible sur cette machine.

Le contrôle teste la construction locale de la définition, la commande vLLM, le refus des
checksums divergents et la synchronisation bloquante du volume d'audit. Il ne construit pas
l'image distante, ne réserve pas de GPU, ne crée pas de volume ou de secret et n'envoie aucune
requête à Modal.

## Limites de la preuve

La compatibilité réelle de l'image vLLM, le téléchargement du volume, le démarrage T4, l'URL,
le Bearer token, le smoke test FR/EN, la persistance distante, la CD et l'arrêt de facturation
restent non prouvés. Ils nécessitent une autorisation explicite et une observation côté
fournisseur.
