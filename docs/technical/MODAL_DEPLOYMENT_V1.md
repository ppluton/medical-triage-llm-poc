# Déploiement privé Modal v1

- Date : 2026-09-16
- Statut : `implemented_locally_not_deployed`
- Sources : [serveur vLLM Modal](https://modal.com/docs/examples/vllm_inference),
  [serveurs Modal](https://modal.com/docs/guide/servers),
  [volumes](https://modal.com/docs/guide/volumes),
  [mise à l'échelle](https://modal.com/docs/guide/scale) et
  [déploiement continu](https://modal.com/docs/guide/continuous-deployment).

## But et limites

`deploy/modal_app.py` prépare une cible T4 pour la démonstration pédagogique. Un seul
conteneur conserve deux environnements Python séparés : vLLM écoute uniquement en boucle
locale et la factory FastAPI authentifiée est le seul serveur exposé. Cette séparation reprend
la recette réellement vérifiée par Kaggle v37 et évite de modifier les dépendances de vLLM.
Le nombre de conteneurs est limité à un, le minimum vaut zéro et la fenêtre d'inactivité
vaut 120 secondes. Cette configuration limite le risque de coût oublié ; elle ne constitue
pas un plafond de facturation fournisseur.

La définition est locale et n'a créé aucune ressource Modal. Elle ne prouve ni compatibilité
GPU sur cette cible, ni URL accessible, ni CD exécutée, ni performance clinique. Le
déploiement demeure soumis au choix et au plafond de coût approuvés par Pierre.

## Identité des artefacts

Le démarrage rehash les onze fichiers du snapshot Base avant de lancer vLLM. Le manifeste,
la révision, la licence Apache-2.0 et le poids de 3,2 Gio doivent correspondre à la ressource
Kaggle privée déjà vérifiée. Les cinq fichiers utiles du SFT v39 sont également rehashés ;
l'adaptateur attendu porte le SHA-256
`c911f9c631be825f4af5c7dff5a87409d1ee91d4c28e2b0b1571e808e055d413`.
DPO n'est ni monté ni servi.

Le volume `chsa-triage-models-v1` est monté en lecture seule avec les chemins suivants :

```text
/models/base/MODEL_SNAPSHOT_MANIFEST.json
/models/base/model.safetensors
/models/adapter/adapter_model.safetensors
/models/adapter/adapter_config.json
/models/adapter/tokenizer.json
/models/adapter/tokenizer_config.json
/models/adapter/chat_template.jinja
```

Tout checksum divergent bloque le démarrage avant l'ouverture de l'API.
Le [manifeste de transfert](../../data/manifests/modal-deployment-assets-v1.json) conserve
l'identité des deux couches, du runtime et des ressources attendues sans chemin local ni secret.

## Préparation locale, sans création cloud

Le snapshot source existe dans le cache Hugging Face local à la révision exacte. Pour créer
un dossier matériel neuf sur le même volume que ce cache, utiliser un chemin explicite encore
absent, puis vérifier le manifeste attendu :

```bash
.venv/bin/python scripts/build_kaggle_model_snapshot.py \
  --snapshot /absolute/path/to/huggingface/snapshots/e249956c10337100486d07afb77e3eb2b30906b8 \
  --output /absolute/path/to/chsa-modal-stage-v1/base \
  --revision e249956c10337100486d07afb77e3eb2b30906b8 \
  --expected-model-sha256 6df85b39330e5a425ee36253d0f894e4387e4f0a15b9c53cb467d668e6b3a841 \
  --dataset-id pierrepluton/qwen3-1-7b-base-e249956c

shasum -a 256 /absolute/path/to/chsa-modal-stage-v1/base/MODEL_SNAPSHOT_MANIFEST.json
```

Le résultat exigé est
`920a5897431d1dfc62502815c5ec4929a149d5f324e6f5b2b3d86db4a691f0d1`.
Copier ensuite dans un nouveau dossier `adapter` uniquement les six fichiers déclarés par
`data/manifests/sft-v39-kaggle-private-v1.json`, puis exécuter
`verify_selected_adapter` avant tout transfert. Aucun token ne doit être placé dans ce
dossier.

## Opérations externes après autorisation

Ces commandes créent ou modifient des ressources externes. Ne pas les exécuter avant
l'autorisation explicite du fournisseur et du budget :

```bash
modal volume create chsa-triage-models-v1 --version=2
modal volume create chsa-triage-audit-v1 --version=2
modal volume put chsa-triage-models-v1 /absolute/path/to/chsa-modal-stage-v1/base /
modal volume put chsa-triage-models-v1 /absolute/path/to/chsa-modal-stage-v1/adapter /
modal secret create chsa-triage-api-v1 TRIAGE_API_TOKEN="$TRIAGE_API_TOKEN"
modal deploy -m deploy.modal_app
```

Le secret `chsa-triage-api-v1` doit contenir un jeton aléatoire d'au moins 32 caractères. Le
token Modal et le token applicatif restent distincts. Le endpoint HTTPS est routable mais
refuse toute requête sans `Authorization: Bearer ...`.

## Smoke test et audit

Après déploiement, exécuter les deux scénarios synthétiques FR/EN :

```bash
.venv/bin/python scripts/evaluate_triage_endpoint.py \
  --url "$TRIAGE_MODAL_URL" \
  --scenarios data/samples/modal-smoke-scenarios.json \
  --output /chemin/prive/modal-smoke.json
```

Télécharger ensuite l'audit privé dans un emplacement contrôlé et le rapprocher du rapport
avec `scripts/verify_endpoint_audit.py`. Les identifiants doivent correspondre exactement.
Le fichier et son dossier de volume sont synchronisés avant restitution de chaque réponse ;
un échec de synchronisation bloque la réponse.

## Déploiement continu borné

`.github/workflows/deploy-modal.yml` est uniquement manuel (`workflow_dispatch`) et utilise
l'environnement GitHub `modal-demo`. Cet environnement doit exiger une approbation et fournir
`MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET`, `TRIAGE_API_TOKEN` et la variable
`MODAL_ENVIRONMENT`. L'URL n'est pas un secret à préconfigurer : après le premier déploiement,
le workflow la résout depuis `modal.Server.from_name(...).get_url()`, valide son origine HTTPS,
puis lance les deux scénarios synthétiques. Il ne
publie pas l'audit ni le token comme artefacts.

Après la démonstration, arrêter ou supprimer le déploiement selon la procédure Modal, puis
vérifier côté fournisseur que zéro conteneur reste actif. La suppression des volumes est une
décision distincte car elle efface les poids et l'audit.
