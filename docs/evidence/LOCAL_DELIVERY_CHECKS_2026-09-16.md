# Contrôles locaux avant livraison

Date : 2026-09-16 — Statut : draft
Sources : régression `val_3a9e9d0cf24e`, contrôle de page `val_4a696a1065d0`, inventaire Git et scan local.

La régression complète à la révision a66a3e2 passe 171 tests en 29,87 secondes, avec un avertissement Starlette/httpx. Ruff passe sur src, scripts et tests. Les changements de main liés à la page de présentation ont ensuite été intégrés sans conflit ; les assets existants sont conservés.

Le contrôle de 450 fichiers suivis ne trouve aucun fichier sous les répertoires interdits de données brutes, aucun poids/checkpoint/journal et aucun fichier de plus de 10 Mo. Les motifs recherchés de clés privées et jetons usuels n'ont aucun résultat ; ce scan n'est pas une détection exhaustive des secrets ou données personnelles.

Les README, l'index des livrables et le rapport sont actualisés avec les résultats QA v35. Les liens locaux des documents d'entrée sont valides. Le diagnostic abandonné non suivi a été déplacé dans une archive locale ignorée, sans suppression de son contenu.

La page statique locale affiche le corpus corrigé, le SFT 500 et les métriques finales. Le HTML servi correspond au fichier du checkout ; DOM et rendu ont été inspectés dans le navigateur intégré. À une largeur de 1600 pixels, la largeur du contenu est également 1600 ; la section de preuves est unique. La capture pleine page présentait des répétitions d'assemblage ; elle n'est pas utilisée comme artefact de livraison. L'onglet temporaire est fermé et le serveur de validation arrêté, port 3055 libéré.

Ces résultats sont locaux. Ils ne prouvent ni une CI distante, ni une publication de la page, ni l'accessibilité extérieure de l'API. La v36 est en cours et la présentation PowerPoint reste à finaliser.
