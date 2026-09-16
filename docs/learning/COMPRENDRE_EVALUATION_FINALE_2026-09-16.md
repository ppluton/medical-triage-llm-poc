# Ce que nous apprend l'évaluation finale

Date : 2026-09-16 — Statut : draft
Sources : docs/evidence/FINAL_QA_V35_RESULT.md ; protocole final figé.

Nous avons donné aux trois modèles les mêmes 500 exemples, gardés à part pendant leur entraînement. Le SFT obtient une perte de 0,844 contre 1,575 pour la Base : il donne davantage de probabilité aux réponses attendues du corpus. Cela répond à la question « a-t-il appris quelque chose qui se retrouve sur des exemples non utilisés pour l'entraîner ? ».

Le DPO obtient 0,843. C'est très proche du SFT ; 43 réponses générées sur 50 sont même identiques. Nous avons bien exécuté l'étape DPO, mais nous ne pouvons pas annoncer qu'elle améliore sensiblement le triage. Un résultat négatif ou modeste fait partie de l'expérience et doit apparaître dans le rapport.

La perte n'est pas un pourcentage de bonnes réponses. Pour savoir si le prototype pose les bonnes questions et propose une priorité pertinente, nous testons séparément le parcours API sur des scénarios synthétiques. La comparaison de connaissances et la démonstration du parcours répondent à deux questions différentes.

Le protocole final a été figé avant le test. Nous ne nous servons pas de ces 500 exemples pour retoucher le modèle après avoir vu ses réponses : sinon ils cesseraient d'être une évaluation indépendante.
