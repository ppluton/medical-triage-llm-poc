# Lancement de la réserve sélectionnée — Kaggle v44

- Date : 2026-09-16
- Statut observé : `RUNNING`
- Notebook privé : `pierrepluton/chsa-source-sft-qwen3`, version 44
- Candidat : SFT v39, étape 150
- Notebook SHA-256 : `fe84e617b5a4fb413fcbab260bc0b526eaae76d3639911ba1ae08b658191415a`
- Décision SHA-256 : `cc4b4d5041c72cde22182b6bad0eb87aaf758830ea0c25f4f2f9441bfc1e2455`
- Optimisation : 0 étape
- Réserve synthétique : 18 scénarios, première ouverture autorisée

## Préflight

Le bundle décompressé contient 21 fichiers. Le runner embarqué appelle explicitement
`verify_base_snapshot` avant le chargement du modèle et contient la décision SFT exacte. Le
notebook monte uniquement les trois ressources privées Base, SFT v39 et DPO v41 ; aucune
ancienne version de notebook n’est utilisée comme source.

Un premier assert de préflight local a échoué après avoir cherché à tort le nom du
vérificateur dans la chaîne bootstrap compressée ; la commande shell a néanmoins poursuivi le
push. Le contrôle corrigé décompresse le bundle réellement envoyé, vérifie le runner, la
décision et le SHA-256 du notebook. Il passe avant l’observation `RUNNING`. L’incident ne
modifie ni le notebook, ni les données, ni le modèle.

## Portée

Cette version évalue uniquement le SFT sélectionné sur la réserve. Elle n’entraîne rien et ne
compare plus DPO après lecture de la réserve. Son statut `RUNNING` ne prouve encore ni
chargement réussi, ni génération, ni résultat final.
