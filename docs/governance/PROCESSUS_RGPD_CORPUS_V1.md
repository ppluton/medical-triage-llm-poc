# Processus de protection des données du corpus

Date : 2026-09-16 — Statut : proposed, justification de POC ; revue juridique non réalisée

Sources : [CNIL — anonymisation](https://www.cnil.fr/fr/technologies/lanonymisation-de-donnees-personnelles), [CNIL — données de santé](https://www.cnil.fr/fr/quest-ce-ce-quune-donnee-de-sante), [CNIL — exigences générales](https://www.cnil.fr/fr/sante-exigences-generales), [Presidio Analyzer](https://microsoft.github.io/presidio/analyzer/), [Presidio Anonymizer](https://microsoft.github.io/presidio/anonymizer/), [politique technique](../technical/ANONYMISATION_V1.md).

## Périmètre et position prudente

Le POC utilise des corpus éducatifs publics à révisions épinglées et des scénarios synthétiques. Aucune donnée hospitalière réelle n’est autorisée dans ce dépôt. Les textes médicaux peuvent néanmoins contenir des informations identifiantes ou des quasi-identifiants : leur disponibilité publique ne supprime pas l’obligation de minimiser le risque.

La CNIL distingue l’anonymisation irréversible de la pseudonymisation, qui peut rester réversible ou recoupable. Un remplacement automatique par jeton et un scan Presidio ne suffisent donc pas, à eux seuls, à certifier un jeu « anonyme au sens du RGPD ». Le projet parle de **contrôles techniques d’anonymisation** et conserve une porte de revue humaine/juridique.

## Chaîne retenue

1. **Minimisation à la source** : conserver uniquement les champs nécessaires à la QA, aux préférences ou à l’évaluation ; exclure les identifiants et les sous-ensembles sans réponse exploitable.
2. **Traçabilité hors texte** : version, licence, checksum, locator et transformations dans les manifestes ; aucune valeur détectée n’est copiée dans les rapports Git.
3. **Détection bilingue** : Presidio `AnalyzerEngine`, `fr_core_news_md` et `en_core_web_sm`, complétés par un recognizer de référence patient.
4. **Remplacement non réversible** : `AnonymizerEngine` avec l’opérateur `replace` et des jetons de type `<EMAIL_ADDRESS>` ou `<PATIENT_REFERENCE>` ; aucune table de correspondance.
5. **Réanalyse fail-closed** : une erreur, une langue non supportée ou une détection résiduelle bloque l’admission automatique.
6. **Revue contextuelle** : les entités `PERSON`, `LOCATION` et `DATE_TIME` sont examinées avec leur contexte, car le NER général confond régulièrement médicaments, protéines, éponymes et lieux. Une détection ambiguë n’est ni supprimée aveuglément ni déclarée sûre sans décision.
7. **Séparation et conservation** : données brutes et artefacts textuels hors Git public ; manifestes et preuves text-free dans Git ; accès local limité au projet ; aucune publication automatique sur Hugging Face.

## État réellement atteint

| Contrôle | État au 16 septembre | Limite |
|---|---|---|
| Modèles spaCy FR/EN installés | observé localement (`fr_core_news_md 3.8.0`, `en_core_web_sm 3.8.0`) | installation locale, pas preuve de rappel exhaustif |
| Intégration Presidio réelle | noms FR/EN, référence patient et emails synthétiques détectés et remplacés ; zéro résidu après correction du faux positif sur placeholder | deux cas synthétiques, pas une mesure de rappel corpus |
| SFT : scan intégral PII | 9 400 champs, 4 700 lignes et les trois splits parcourus ; 1 498 lignes sans détection | détection automatique, pas certification |
| SFT : identifiants directs | 31 détections `PATIENT_NAME` sur 22 lignes masquées dans v2.2 ; rescan direct à zéro | contrôle technique, pas certification juridique |
| SFT : contexte | 3 199 lignes v2.2 conservent seulement `PERSON`, `LOCATION` ou `DATE_TIME` sous politique source publique | auteurs, éponymes, lieux et durées possibles ; publication bloquée |
| SFT : contenu transformé | 31 remplacements positionnels vérifiés ; 4 700 lignes conformes au schéma v2.2 | aucune validation clinique |
| DPO : identifiants directs | statut technique et revue éducative présents sur 480 lignes | lot anglais ; aucune revue professionnelle revendiquée |
| DPO : contexte | scan complémentaire et exclusions documentés | les alertes NER ambiguës ne valent pas certification |
| Données patient réelles | aucune autorisée ni intégrée | tout changement de périmètre exige une gouvernance distincte |

## Données, finalité et durée

- **Finalité** : démonstration pédagogique de préparation SFT/DPO et d’un POC de triage ; aucune prise de décision clinique réelle.
- **Données nécessaires** : instruction, réponse ou préférence, langue, provenance, split, transformation et statuts de revue. Les métadonnées cliniques absentes restent nulles ; elles ne sont pas déduites pour remplir un tableau.
- **Stockage** : sources brutes et JSONL lourds dans les espaces locaux privés contrôlés ; dépôt public limité aux schémas, petits exemples synthétiques, manifestes et métriques text-free.
- **Conservation** : aucune durée juridique définitive n’est fixée par ce document. Avant une collecte réelle, le responsable de traitement doit définir base légale, durée, droits, accès, sécurité, éventuelle AIPD et procédure de suppression.

## Porte de publication

Un artefact ne peut être présenté comme anonymisé et prêt à diffuser que si :

- la source et la licence autorisent l’usage prévu ;
- les scans directs et contextuels sont terminés ;
- les alertes ont une décision de revue traçable ;
- aucune donnée réelle non autorisée n’est présente ;
- le canal, l’audience, la durée et les accès sont approuvés ;
- la formulation publique distingue contrôle technique, anonymisation juridique et validation clinique.

La [finalisation v2.2](../evidence/SFT_PRIVACY_FINALIZATION_2026-09-16.md) franchit la
porte technique pour l'entraînement pédagogique contrôlé : toutes les alertes directes sont
masquées et les alertes contextuelles reçoivent une disposition text-free. La publication
pédagogique sur Hugging Face est décidée par
l'[ADR-022](../decisions/ADR-022-publier-dataset-et-adaptateurs-hugging-face.md) : sources déjà
publiques sous licences ouvertes, sans donnée patient réelle.
Cette documentation justifie la méthode suivie et ses limites ; elle ne délivre pas une
certification RGPD.
