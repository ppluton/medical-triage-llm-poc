# Comprendre la sélection du modèle avant le test final

- Date : 2026-09-16
- Statut : `draft`
- Sources : `docs/technical/SELECTION_MODELE_RESERVE_V1.md`, `docs/evidence/TRIAGE_RESERVE_V1_FREEZE_2026-09-16.md`

## Ce qui a été fait

Une chaîne distincte a été ajoutée pour choisir entre SFT et DPO sur les données de
développement, puis évaluer une seule variante sur une réserve encore non observée. Elle
comprend une revue aveugle, une règle de décision versionnée, des contrôles de checksum et un
runner Kaggle séparé.

## Pourquoi c’était nécessaire

Regarder le résultat final avant de choisir le modèle transforme ce résultat en validation et
fait perdre son indépendance au jeu. Relancer ensuite un entraînement ou modifier un prompt à
partir de cette mesure serait une fuite de test, même si aucun exemple n’est copié dans le
train.

Le DPO n’est pas automatiquement meilleur parce que sa loss de préférence baisse. Il peut
modifier le style sans améliorer le triage, ou améliorer un indicateur tout en dégradant la
terminaison, le format ou les affirmations non étayées. La sélection doit donc précéder la
réserve et s’appuyer sur plusieurs observations comparables.

## Comment la décision fonctionne

La comparaison dite de Pareto évite d’inventer une note globale ou des coefficients cliniques.
Pour retenir DPO, aucune métrique suivie ne doit se dégrader par rapport au SFT et au moins une
doit progresser. Sinon, le SFT est préféré parce qu’il est plus simple et que le bénéfice du
DPO n’est pas démontré.

Une file aveugle masque les noms Base/SFT/DPO pendant la lecture qualitative. Les flags portent
sur les faits cliniques non étayés, les diagnostics ou prescriptions, les délais dangereux et
les sorties malformées ou répétitives. Cette lecture reste une revue de projet, pas un avis de
professionnel de santé.

## Notions à retenir

- Un jeu de développement sert à choisir ; une réserve sert à estimer une dernière fois.
- Une loss d’entraînement n’est pas une métrique clinique.
- À égalité, une solution plus simple est préférable à une étape DPO sans gain prouvé.
- Le checksum protège l’identité d’un artefact, pas sa qualité médicale.
- Un résultat négatif est utile s’il empêche de complexifier inutilement le modèle livré.

## Questions encore ouvertes

- La v43 montrera-t-elle une différence entre le nouveau SFT v39 et le DPO v41 ?
- Combien de sorties resteront signalées lors de la revue de projet aveugle ?
- Le candidat sélectionné conservera-t-il son comportement sur les dix-huit cas de réserve ?
- Une validation clinique indépendante confirmerait-elle ou contredirait-elle les références
  proposées du POC ?
