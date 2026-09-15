# Finalisation technique de la confidentialité SFT v2.2

- Date : 2026-09-16
- Statut : preuve passée pour entraînement pédagogique contrôlé ; publication interdite
- Manifeste : [SFT v2.2](../../data/manifests/derived-source-medical-qa-sft-v2.2-privacy-finalized.json)
- Résultat compact : [JSON compagnon](SFT_PRIVACY_FINALIZATION_2026-09-16.json)
- Statut juridique : aucune certification RGPD
- Statut clinique : aucune validation clinique

## Question traitée

Le candidat SFT peut-il franchir la porte technique de confidentialité pour un entraînement
local contrôlé sans effacer aveuglément les termes médicaux signalés par le NER général ?

## Transformation observée

Le scan positionnel `val_9732827ea426` a reproduit les 31 détections `PATIENT_NAME`
sur 22 lignes du corpus v2.1. Le code au commit `ff158aa` a vérifié les checksums de
l'entrée et des findings, vérifié chaque intervalle contre le texte exact, puis remplacé
chaque occurrence par `<PATIENT_NAME>`. La v2.1 n'a pas été modifiée.

La dérivation v2.2 conserve 4 700 lignes : 3 721 train, 479 validation et 500 test.
Le preflight vérifie les hashes, la couverture exacte de train/validation, la conformité
des 4 700 lignes au schéma v2.2 et l'absence du test dans les fichiers d'entraînement.

## Rescan indépendant

Le job `val_8d3b6c685c05` a rescanné les 9 400 champs de v2.2 et s'est terminé avec le
code 0. Aucune entité directe `PATIENT_NAME`, téléphone, email, carte, IBAN, IP ou
référence patient n'est présente dans le résultat. Il reste 3 199 lignes avec uniquement
des candidats `PERSON`, `LOCATION` ou `DATE_TIME`; 1 501 lignes n'ont aucune détection.

Ces candidats contextuels sont conservés sous une décision technique explicite : les sources
sont des corpus médicaux publics épinglés, aucun corpus patient réel n'est autorisé, et le
masquage global des auteurs, éponymes, lieux anatomiques ou durées dégraderait le contenu.
Chaque décision reste reliée à l'identifiant, au split et aux comptes d'entités dans un
artefact local text-free.

## Ce que la preuve autorise

- utiliser v2.2 pour un entraînement SFT pédagogique local et contrôlé ;
- charger seulement les 3 721 lignes train et 479 validation ;
- conserver les 500 lignes test isolées ;
- comparer un futur checkpoint au corpus et au commit enregistrés.

## Ce qu'elle n'autorise pas

La preuve n'autorise pas la publication du dataset comme « anonymisé RGPD », l'emploi de
données hospitalières, une conclusion de sûreté clinique ou une diffusion publique. Une
revue humaine/juridique indépendante reste requise avant toute publication ou changement
de finalité.
