# Filtrage du candidat DPO après revue contextuelle

- Date : 2026-09-12
- Statut : draft — nouveau candidat filtré, pas d'approbation clinique ni d'entraînement
- Sources : [scan contextuel](DPO_CONTEXT_SCAN_2026-09-12.json), [exclusions](../../data/manifests/dpo-review-exclusions-v1.json), [résumé du candidat](DPO_FILTERED_CANDIDATE_2026-09-12.json).
- Environnement : macOS, branche `codex/complete-poc-evaluation` ; entrées/sorties hors Git dans `artifacts/dpo-candidates-v2` et `artifacts/dpo-candidates-v3-filtered`.

## Constat et décision

La revue d'extraits a confirmé des signatures et noms dans des récits personnels,
y compris des éléments non reconnus par le NER général. Le seul scan des
identifiants directs n'était pas suffisant. Le lot initial était resté candidat :
aucun DPO n'a été entraîné avec ces paires.

La première passe de recherche de récits personnels a identifié 97 prompts.
La lecture a conservé quatre faux positifs académiques (`train-249`, `train-314`,
`train-421`, `dev-10`) et exclu les 93 récits personnels restants. La revue des
prompts hors des formes académiques habituelles a ajouté `train-84` et `train-445`.
Ces 95 exclusions portent le motif `unverified_personal_health_narrative` : elles
ne prétendent pas établir l'identité ou l'authenticité d'une personne.

La paire `train-232` est également exclue car une pagination bibliographique avait
été altérée par un masque de téléphone. Aucun chiffre ni corrigé n'est inventé
pour la restaurer. Le total est **96 exclusions**, sans remplacement par de
nouvelles lignes. Les noms et textes personnels ne sont pas publiés dans le registre.

## Résultat vérifié

Le candidat filtré contient **426 train et 54 validation**, toujours en anglais.
Les lignes retenues sont identiques octet pour octet aux lignes de départ et
restent dans le même ordre et le même split. Les labels de préférence sont inchangés.
Le registre relie chaque exclusion à l'empreinte de sa ligne source et au manifeste
parent. Les fichiers originaux restent intacts.

La liste de protection ajoute les hashes des 4 700 prompts SFT v2.1 aux hashes
historiques. Le validateur structurel, la vérification des doublons et l'exclusion
des prompts protégés passent sur le lot filtré, avec `require_review=False` : ce
paramètre explicite montre que ces contrôles ne valent pas approbation des données.
Aucune réponse du jeu de test final n'est utilisée pour sélectionner une préférence.

## Limites et suite

La recherche textuelle sert au repérage, pas à une certification d'anonymisation.
Les durées, noms de médicaments, protéines, auteurs bibliographiques et éponymes
ne sont pas supprimés aveuglément. Les préférences demeurent des préférences
biomédicales sources, pas des labels cliniques de triage. La décision d'usage
éducatif et la revue de contenu restantes doivent être explicites avant le DPO.
