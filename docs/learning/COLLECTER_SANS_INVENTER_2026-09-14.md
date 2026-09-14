# Collecter sans transformer une inconnue en absence

Date : 2026-09-14 — Statut : draft
Sources : ADR-015 ; docs/technical/COLLECTE_COMPLEMENTAIRE_V1.md ; résultat v34.

Le modèle répondait au format demandé, mais oubliait de poser des questions dans les cas incomplets. Nous avons donc ajouté à l'application un suivi explicite des rubriques renseignées. C'est une responsabilité du parcours utilisateur, qui ne nécessite pas de réentraîner le modèle.

La distinction essentielle est entre « aucune allergie déclarée », « nous n'avons pas demandé » et « l'information est indisponible ». Une liste vide ne permet pas de choisir entre ces situations. Le contexte transporte désormais les absences explicitement déclarées et les informations indisponibles, sans inventer une réponse.

À chaque tour, le client conserve le contexte, ajoute les nouvelles réponses et rappelle la même API. L'application propose les prochaines rubriques non traitées en français ou en anglais ; une rubrique renseignée n'est plus demandée. La proposition de priorité reste produite par le modèle. Une urgence éventuelle n'attend donc pas la fin du questionnaire.

Les tests locaux parcourent trois échanges synthétiques et contrôlent la trace de chaque réponse. Ils vérifient aussi que les nouveaux champs de texte passent par l'anonymiseur avant transport et journalisation. Le fournisseur et le détecteur utilisés dans ces tests sont simulés : c'est une preuve du raccord logiciel, pas une nouvelle mesure clinique ni GPU.

Il reste à vérifier la pertinence des questions et du triage avec le vrai modèle, puis à montrer ce parcours dans la démonstration. Une rubrique remplie peut contenir une réponse vague ou contradictoire ; le suivi des champs ne résout pas cette interprétation médicale. Le test final de connaissances lancé avant cette modification reste inchangé.
