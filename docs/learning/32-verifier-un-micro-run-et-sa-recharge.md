# Vérifier un micro-run et sa recharge

- **Date :** 2026-09-11
- **Statut :** draft
- **Sources :** ADR-011 ; SFT_MICRO_RUNS_2026-09-11.md ; TERMINATION_MICRO_V15_RESULT.json.

## Ce qui a été fait et pourquoi

Nous avons repris le SFT v5 pendant 20 étapes sur 64 exemples, avec une terminaison EOS corrigée. Le but était de tester une correction bornée avant de consommer plusieurs heures de GPU. Les trois exemples de validation servent au développement ; le test final reste isolé.

## Comment la preuve est obtenue

Le script contrôle les hashes, les labels après collation, les générations avant/après, les changements effectifs des tenseurs LoRA et leur finitude. Il sauvegarde le tokenizer avec le même format, libère le modèle, recharge une base épinglée puis les poids exportés, et compare les tokens générés. Recharger un objet Python encore en mémoire n'aurait pas constitué cette preuve.

Avant le micro-run, les trois réponses atteignaient 256 tokens. Après, elles se terminent par EOS après 20, 67 et 10 tokens. Les sorties rechargées sont identiques. Cela démontre que la chaîne courte entraîne, exporte et recharge le modèle dans cet environnement.

## Ce que cela ne prouve pas

Une réponse peut s'arrêter correctement tout en étant hors sujet. C'est le cas de la question v1 dont les choix QCM avaient disparu : le modèle ne disposait pas du contexte nécessaire. La prochaine expérience utilise donc les mêmes contrôles avec le corpus v2 complet en contexte. Nous n'avons pas exécuté de continuation témoin au format original ; attribuer chaque changement au seul EOS serait trop fort.

Une meilleure loss ou moins de répétitions ne signifie pas que les informations médicales sont correctes. Il faut comparer sur un protocole commun, lire les réponses et conserver les limites de validation clinique. Le DPO ne doit pas servir à masquer un défaut technique non compris.

## Notions pratiques

Kaggle limite la taille du code d'un notebook. Pour un micro-test, transporter seulement les 64+3 exemples retenus, avec leurs hashes et leur filiation vers le corpus complet vérifié, suffit. Le sous-ensemble reste distinct d'un pré-vol de tout le corpus sur GPU. Le notebook et les poids restent privés et les données lourdes restent hors Git.

## Ce que les essais v16 et v17 ajoutent

Le corpus v2 restaure les choix des QCM. Le v17 vérifie ensuite sur la GPU que seuls les tokens de réponse contribuent à la loss. Dans les deux cas, les sorties s'arrêtent et la sauvegarde/recharge conserve les tokens, mais les deux réponses QCM divergent des références. Une chaîne d'entraînement techniquement correcte ne suffit donc pas à produire de bonnes réponses. Les losses full/completion ne mesurent pas exactement la même chose.

La prochaine étape est une comparaison figée sur 30 nouvelles générations de validation et 500 mesures de loss. Ce protocole est préparé, pas encore exécuté ; la validation clinique et le DPO restent à faire. Voir la preuve professionnelle du 11 septembre.
