# Résultat v26 : effet de la consigne explicite

- Date : 2026-09-12
- Statut : draft — mesure GPU terminée ; validation clinique non effectuée
- Sources : [lancement](TRIAGE_V26_LAUNCH_2026-09-12.md), [mesures et hashes](TRIAGE_V26_RESULT_2026-09-12.json), [v25](TRIAGE_V25_RESULT_2026-09-12.md).

Version Kaggle privée 26, scriptVersionId 349329192, état COMPLETE. Même Base,
même SFT 500, même runtime T4, mêmes 18 scénarios de développement que v25 ;
consigne `triage-demo-v3-proposed` explicitant les priorités. Zéro entraînement,
zéro test final. Recharge : 30/30 générations QA identiques. Les agrégats sont
recalculés localement par `score_outputs` et égaux au résumé GPU.

| Mesure sur 18 scénarios | Base v26 | SFT v25 | SFT v26 |
|---|---:|---:|---:|
| JSON conforme | 0 | 10 | 12 |
| Priorité conforme à la référence proposée | 0 | 4 | 6 |
| Sortie valide et maximum correct sur les 6 critiques | 0 | 2 | 2 |

Le gain de format et d'accord est descriptif sur ce petit lot de développement.
Les deux cas respiratoires obtiennent `moderate` au lieu du `maximum` proposé,
malgré la description du signal explicite dans la consigne. Le cas de douleur
thoracique EN obtient la bonne priorité mais invente un âge précis, des antécédents,
des traitements et des constantes stables. Un bon label ne suffit donc pas à rendre
la réponse fidèle. Le cas d'informations insuffisantes EN reste `deferred` malgré
une justification qui reprend la définition de `moderate`.

Le défaut de recharge est résolu ; la qualité du triage reste insuffisante. Aucun
score clinique, aucune acceptation d'usage patient, aucun effet DPO n'est établi.
Conserver cette consigne pour la comparaison expérimentale DPO, puis mesurer
séparément le serveur avec décodage contraint et garde-fous. Ne pas multiplier les
ajustements sur le même petit lot ni présenter le DPO comme une correction garantie.

Récupération : `kaggle kernels output pierrepluton/chsa-source-sft-qwen3/26 -p artifacts/kaggle/triage-v26-reports --page-size 200 --file-pattern '.*(triage-base-sft-v26/.*\.json|\.log)$'`.
Les textes bruts restent hors Git ; empreintes des entrées dans le JSON associé.
