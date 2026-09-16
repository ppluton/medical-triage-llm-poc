# Comprendre la séparation Cloudflare Pages / Modal

- Date : 2026-09-16
- Statut : `draft`
- Sources : [ADR-021](../decisions/ADR-021-separer-frontend-cloudflare-backend-modal.md) et
  [recette technique](../technical/CLOUDFLARE_PAGES_FRONTEND_V1.md).

## Ce qui a été fait

L'interface FastAPI existante a été transformée en build statique reproductible. Une Pages
Function contrôle l'accès et transmet seulement les requêtes de triage au backend Modal. Le
build et le proxy ont été testés localement, puis le paquet a été préparé sur le bon compte
Cloudflare sans déclarer la publication terminée.

## Pourquoi

Un GPU ne doit pas démarrer pour livrer trois petits fichiers web. Séparer les actifs
statiques rend l'ouverture immédiate et réserve les crédits Modal aux appels du modèle. Le
proxy empêche aussi d'inscrire le jeton Modal dans du JavaScript visible par tous.

## À retenir

- héberger une page et héberger un modèle sont deux problèmes différents ;
- un secret présent dans le JavaScript n'est plus un secret ;
- un proxy doit échouer fermé si sa configuration manque ;
- le sous-domaine stable prouve l'accès au frontend, pas le fonctionnement du GPU ;
- le smoke test final doit traverser Cloudflare, Modal, FastAPI, vLLM et l'audit.

## Questions encore ouvertes

- durée de validité et mode de remise du jeton jury ;
- durée de conservation de l'audit distant ;
- temps de préchauffage Modal à retenir pour la soutenance ;
- arrêt et suppression éventuelle des volumes après récupération des preuves.
