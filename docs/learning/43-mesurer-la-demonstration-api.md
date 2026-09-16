# Préparer une mesure de la démonstration complète

- Date : 2026-09-12
- Statut : draft
- Source : [guide du runner d'endpoint](../technical/EVALUATION_ENDPOINT_V1.md).

Une réponse correcte dans un notebook ne prouve pas que l'application complète fonctionne. Nous avons préparé un programme qui enverra les scénarios fictifs à l'API et vérifiera les réponses, leur temps d'arrivée et leurs identifiants.

Il faut conserver les échecs dans les mesures : une API très rapide parce qu'elle retourne des erreurs n'est pas une démonstration réussie. Le p95 décrit le temps sous lequel arrivent environ 95 % des requêtes de ce lot ; sur un petit lot, ce chiffre reste descriptif.

Les tests actuels utilisent un transport simulé pour vérifier que le programme détecte effectivement les erreurs. Les mesures du vrai serveur et la vérification de ses journaux seront des preuves distinctes, encore à produire.

## La preuve d'audit est distincte de l'identifiant reçu

Un serveur peut renvoyer un identifiant sans avoir conservé la réponse. Nous avons
ajouté un rapprochement entre le rapport client et le journal serveur : même identifiant,
une seule entrée et contenu identique. Le test passe avec un fichier réellement écrit
par l'API locale et échoue quand on altère son contenu. Il reste à reproduire cela sur
la future démonstration avec le vrai modèle. Cela ne prouve pas encore que le fichier
survivra à un redémarrage du serveur ni que sa durée de conservation est appropriée.
