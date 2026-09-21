# Déploiement pilote Modal du backend vLLM

- Date : 2026-09-16
- Statut : observed — backend déployé et smoke test synthétique réussi
- Environnement : Modal `ppluton/main`, app `chsa-triage-poc`, GPU T4
- Sources : `deploy/modal_app.py`, `data/manifests/modal-deployment-assets-v1.json`, sorties CLI Modal et rapports privés rehashés ci-dessous

## Périmètre et question

Vérifier que le modèle Qwen3-1.7B-Base figé et l'adapter SFT sélectionné peuvent être
chargés depuis des volumes Modal privés, servis par vLLM derrière l'API FastAPI gouvernée,
et audités sans inclure de donnée patient réelle. Cette preuve ne porte ni sur un usage
hospitalier ni sur une validation clinique.

## Identité et configuration observées

- révision Base : `e249956c10337100486d07afb77e3eb2b30906b8` ;
- SHA-256 du poids Base : `6df85b39330e5a425ee36253d0f894e4387e4f0a15b9c53cb467d668e6b3a841` ;
- SHA-256 de l'adapter SFT v39 : `c911f9c631be825f4af5c7dff5a87409d1ee91d4c28e2b0b1571e808e055d413` ;
- image : `vllm/vllm-openai:v0.15.0` épinglée par digest ;
- volumes : `chsa-triage-models-v1` et `chsa-triage-audit-v1` ;
- capacité : T4, un conteneur au maximum, zéro conteneur minimum, extinction après 120 s d'inactivité ;
- origine du service : `<modal-endpoint>` ;
- contrôle applicatif : `proposed-guardrails-v3`.

Le secret Bearer est stocké dans Modal et n'est ni inclus dans Git ni reproduit dans cette
preuve. Le dossier Base distant contient les 13 fichiers attendus, dont le poids de 3,2 GiB ;
le dossier adapter contient les 6 fichiers attendus. Le démarrage du conteneur a rehashé les
11 fichiers d'identité Base et les 5 fichiers d'identité adapter avant de lancer vLLM.

## Exécution et résultats

Deux scénarios synthétiques bilingues ont été exécutés en série : douleur thoracique FR et
déficit neurologique EN. Le premier passage a révélé que le garde-fou v1 ne rapprochait pas
les signes neurologiques lorsqu'ils étaient fournis dans deux éléments de liste. Le résultat
`moderate` a été conservé comme résultat négatif privé, puis la détection a été corrigée et
versionnée `proposed-guardrails-v2`.

Le smoke public a ensuite révélé une formulation libre ambiguë sur le scénario thoracique
(`attendre` malgré un niveau `maximum`). La version `proposed-guardrails-v3` reconnaît
désormais l'intensité fournie dans un champ séparé et remplace systématiquement la sortie libre
par une formulation déterministe d'évaluation professionnelle immédiate lorsqu'un signal
d'alerte explicite est détecté.

Après redéploiement et attente explicite de `/healthz = 200` :

- 2 requêtes, 2 succès HTTP et contrat, 0 échec ;
- les deux priorités retournées sont `maximum` ;
- le cas neurologique a été corrigé par le garde-fou v2 avec les deux signaux fournis ;
- p50 client : 19 362,01 ms ; p95 client : 31 455,41 ms ;
- 2 identifiants de réponse rapprochés de 2 entrées d'audit privées ;
- coût Modal observé après construction, essais et smoke : 0,05 USD mesuré, 0 USD facturé
  après application des crédits.

Un appel lancé immédiatement après redéploiement a reçu deux réponses `503` pendant le cold
start. La santé est devenue disponible après environ 110 secondes. Le frontend vérifie donc
désormais `/v1/healthz` et affiche une phase de réveil avant d'envoyer une unique requête de
triage. Deux cold starts via le chemin public ont ensuite été observés à 111 et 117,5 secondes ;
la fenêtre frontend est fixée à 190 secondes.

## Vérification publique finale

Sur `https://triage-poc.pierrepluton.com`, avec les scénarios synthétiques intégrés :

- douleur thoracique FR : `maximum`, garde-fou v3 `safe_fallback`, 34 984,70 ms,
  interaction `fcd6ffaf-6ad8-468d-83ef-5f5111fd311f` ;
- déficit neurologique EN : `maximum`, garde-fou v3 `safe_fallback`, 29 567,75 ms,
  interaction `f0334a77-5024-47ac-ab89-b7e80604bab3` ;
- les quatre signaux affichés proviennent des entrées synthétiques ;
- les deux identifiants ont été retrouvés dans le volume d'audit, avec
  `privacy_status=passed` et `schema_validated_not_clinically_validated`.

L'export d'audit privé final porte l'empreinte SHA-256
`2517f80aecfc5b165430d0fb88f622999febe6200910dc10f8dcfc08ca9bcf42`.

## Empreintes des preuves privées

Les rapports contiennent uniquement les scénarios synthétiques, leurs sorties et les audits
anonymisés. Ils restent hors Git ; leurs empreintes permettent de contrôler les exports :

- smoke v2 sain : `525e7697b56e588e8bdb96c481d0e32a7c8f38e78cafaa7d6d48c08a984c875d` ;
- export d'audit : `9c17571dbac96777acac40d111d726a55fdca324db2a07238e6173ac6158496e` ;
- rapprochement : `00f9b8d61cf8a406ecb193d337962c9f0a8a3276e15f9d5c27d14f6d81d39d30`.

## Ce que cette preuve établit

- la reproductibilité de l'identité Base + SFT et l'échec fermé sur checksum ;
- le démarrage réel de vLLM sur T4 et l'exécution de l'API FastAPI ;
- le contrat de réponse, la protection Bearer et la traçabilité sur deux cas synthétiques ;
- la correction déterministe du scénario neurologique séparé en plusieurs symptômes.
- le chemin public complet Cloudflare Pages → Modal → FastAPI/vLLM → audit privé ;
- la neutralisation déterministe du texte libre pour les signaux d'alerte proposés.

## Limites

- deux scénarios ne constituent ni une évaluation de robustesse ni une validation clinique ;
- les priorités et règles restent `proposed` jusqu'à validation par un professionnel de santé ;
- la latence observée ne constitue pas encore un benchmark en charge ;
- le cold start est incompatible avec une attente instantanée et doit être annoncé en démo ;
- les volumes persistants peuvent générer un coût de stockage même sans GPU actif ;
- l'endpoint public reste un pilote pédagogique protégé par token, pas une mise en production.
