# Comprendre la séparation Cloudflare Pages / Modal

- Date : 2026-09-16
- Statut : `observed`
- Sources : [ADR-021](../decisions/ADR-021-separer-frontend-cloudflare-backend-modal.md) et
  [recette technique](../technical/CLOUDFLARE_PAGES_FRONTEND_V1.md).

## Ce qui a été fait

L'interface FastAPI existante a été transformée en build statique reproductible. Une Pages
Function contrôle l'accès et transmet seulement les requêtes de triage au backend Modal. Le
build et le proxy ont été testés localement, puis publiés sur le bon compte Cloudflare et sur
`triage-poc.pierrepluton.com`. Deux scénarios synthétiques ont traversé le chemin complet.

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
- Cloudflare Workers n'accepte pas `redirect: "error"` : il faut utiliser `manual` puis refuser
  explicitement les statuts 3xx ; les logs temps réel ont permis de le prouver ;
- un timeout de deux minutes était trop serré ; 190 secondes couvre les cold starts observés
  sans maintenir un GPU chaud en permanence.

## Questions encore ouvertes

- durée de validité et rotation du jeton jury après la soutenance ;
- durée de conservation de l'audit distant ;
- préchauffage volontaire juste avant la soutenance ou démonstration visible du cold start ;
- arrêt et suppression éventuelle des volumes après récupération des preuves.
