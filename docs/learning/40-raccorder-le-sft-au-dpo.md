# Passer le bon modèle à l'étape suivante

- Date : 2026-09-12
- Statut : draft
- Source : [preuve du raccord DPO](../evidence/DPO_HANDOFF_2026-09-12.md).

Nous avons remplacé une référence fixe à l'ancien SFT par un manifeste qui identifie le modèle choisi et son tokenizer. Le tokenizer est le dictionnaire et le format de lecture du modèle : transmettre les bons poids avec un autre format pourrait fausser l'expérience.

La vérification compare les empreintes des fichiers et relie la comparaison Base/SFT au même modèle. Des tests s'assurent qu'un fichier modifié ou la comparaison d'un autre checkpoint sont refusés. Le contrôle effectué sur les vraies paires DPO confirme également qu'elles tiennent dans la longueur disponible, sans couper les réponses.

Ce travail répare un raccord technique. Il ne prouve pas encore que DPO améliore le modèle : cela nécessite la revue des préférences, un entraînement et une comparaison. Nous conservons ces étapes distinctes pour avancer sans transformer une préparation réussie en résultat inventé.

La première lecture du lot rappelle pourquoi cette distinction compte : une réponse peut être préférée pour son explication alors que les deux réponses choisissent la même option. Les préférences sélectionnées sont anglaises et les réponses choisies sont souvent plus longues. On ne peut donc pas annoncer à l'avance qu'elles rendront l'assistant plus bref, meilleur en français ou compétent en triage ; ce sont des effets à mesurer.

## Revue du 12 septembre : alerte n'est pas suppression

Le scan élargi des 576 paires détecte beaucoup de noms et de durées. Certains noms
sont des médicaments ou des protéines : les remplacer aveuglément dégraderait le
contenu médical. Nous conservons donc les alertes pour revue, sans modifier le lot.
Une pagination bibliographique a déjà subi un faux masquage dans une paire ; sa
correction ou exclusion doit être tracée plutôt que restaurer des chiffres supposés.

Nous avons aussi comparé les prompts DPO au corpus SFT corrigé : aucun doublon
exact normalisé. L'ancienne liste de protection était liée à la v1 et devra être
actualisée dans le manifeste final. Cette vérification n'utilise pas les réponses
du test final et ne détecte pas toutes les paraphrases.

## Filtrer les récits personnels au lieu d'abîmer les connaissances

La revue a effectivement retrouvé des noms et signatures que le premier scan
n'avait pas tous retirés. Pour ce POC, nous avons écarté les récits personnels dont
la gouvernance n'est pas établie, au lieu de conserver des comptes rendus nettoyés
de manière incertaine. Une paire avec citation altérée est également exclue.
Le nouveau candidat contient 426/54 paires ; les lignes retenues sont inchangées.
Les exclusions sont tracées sans publier les éléments personnels. Cette décision
ne transforme pas les préférences restantes en annotations cliniquement validées.

### Vérifier que la référence reste une référence

Le DPO compare une politique qui apprend à une copie du SFT qui sert de repère.
Si les deux changent, le repère bouge et le résultat ne correspond plus à la recette
annoncée. Le runner prend maintenant des empreintes des vrais tenseurs avant/après,
et refuse de déclarer un succès si la référence a changé ou si la politique n'a pas
bougé. Les tests CPU provoquent volontairement ces erreurs. La preuve sur le futur
entraînement GPU reste à obtenir : un contrôle implémenté n'est pas un résultat de run.

### Premier vrai passage dans le trainer, sur un modèle miniature

Le diagnostic CPU a fait deux étapes de DPO sur des préférences synthétiques, avec
un modèle aléatoire minuscule. Les quatre tenseurs de la politique changent et ceux
de la référence restent identiques. Cela vérifie la mécanique TRL/PEFT sans consommer
le quota GPU ni entraîner sur des données non approuvées. Cela ne remplace ni l'essai
CUDA en précision réduite ni l'entraînement du modèle médical.

### Du candidat filtré à l'essai pédagogique

La décision ADR-014 admet les 480 paires filtrées pour une expérience technique,
après les contrôles et exclusions décrits. Les textes ne changent pas : on ne réécrit
pas une préférence pour faire gagner notre modèle. Les métadonnées indiquent une
revue assistée, sans revue clinique indépendante. L'écart avec l'exigence clinique
de la mission demeure ouvert et devra figurer dans le rapport.

La v27 lance vingt étapes sur les vraies préférences sources, depuis le SFT 500.
Le test miniature CPU montrait seulement que le mécanisme des deux adaptateurs
fonctionne. Le nouveau run doit encore prouver ce fonctionnement en FP16/4 bits sur
T4, puis la sauvegarde et la qualité. Il n'est pas un nouveau SFT et ne garantit pas
que les erreurs de triage disparaîtront.

### Sauvegarder les bons poids

Un entraînement terminé peut être suivi d'une mauvaise sauvegarde. Le contrôle
ajouté compare donc le fichier sauvegardé aux poids réellement présents après
l'entraînement, puis la référence initiale au SFT d'origine. Le test modifie
volontairement un fichier pour vérifier que cette divergence est détectée. Même
une sauvegarde exacte devra ensuite être rechargée pour produire des réponses.

### Résultat du premier DPO GPU

La v27 termine ses vingt étapes sans erreur en environ 7 min 44 s, évaluations
comprises. Les poids de la politique changent, la référence reste fixe. La loss de
validation baisse entre les étapes 10 et 20. Cela montre que l'optimisation a eu lieu,
mais pas que le triage s'améliore. L'accuracy TRL de préférence ne doit pas être
présentée comme un pourcentage de bonnes réponses médicales. La prochaine preuve
est la comparaison des réponses produites par Base, SFT et DPO dans les mêmes conditions.
