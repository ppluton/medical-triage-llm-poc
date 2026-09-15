# Étape 46 — Reprendre le corpus sans inventer les preuves

Date : 2026-09-16 — Statut : draft

Sources : [guide de reprise](../../GUIDE_REPRISE.md), [fiche technique active](../technical/CORPUS_ETAPE_1_V1.md), [preuve datée](../evidence/AUDIT_CORPUS_ETAPE_1_2026-09-16.md), consigne de l’étape données.

## Ce qui a été fait

Nous avons repris l’étape données depuis ses résultats attendus : inventaire des quatre sources, corpus SFT bilingue proche de 5 000 lignes, préférences DPO, anonymisation, métadonnées et séparation train/validation/test. Les manifestes, scripts, artefacts locaux et pages amont ont été rapprochés au lieu de s’appuyer uniquement sur les anciens comptes rendus.

## Pourquoi c’était nécessaire

Le dépôt contenait déjà beaucoup de travail, mais plusieurs phrases étaient plus fortes ou plus bloquantes que les preuves disponibles. Le registre disait encore que certaines révisions restaient à épingler alors qu’elles l’étaient déjà. À l'inverse, demander la signature d'un clinicien réel confondait le scénario pédagogique avec un hôpital réel. L’objectif de la reprise est donc de rendre l’état lisible, pas de refaire mécaniquement tous les artefacts ni d'inventer un acteur externe.

## Comment la vérification a été menée

1. Les révisions Git, tailles et empreintes locales ont été comparées aux manifestes.
2. Les 4 700 lignes SFT ont été recomptées par source, langue et split ; les hashes des trois artefacts correspondent.
3. Le pipeline source → canonique → conversation a été rejoué avec les sources locales et le tokenizer figé.
4. Les 480 lignes DPO ont été contrôlées pour leurs hashes et statuts de revue.
5. Un schéma séparé a été ajouté pour les symptômes, antécédents, constantes, provenance et confiance, avec une règle importante : une information absente reste absente.
6. Le processus de protection des données a été documenté en distinguant contrôle Presidio et anonymisation juridique.
7. Un faux positif de la réanalyse Presidio sur le placeholder `<PATIENT_REFERENCE>` a été reproduit avec le modèle français réel puis corrigé sans ignorer les détections hors placeholder.

## Notions à retenir

- **≈ 5 000** n’oblige pas à réintroduire 300 lignes à risque : 4 700 exemples isolés et intacts valent mieux que 5 000 obtenus par remplissage.
- **QA médicale ≠ triage** : une réponse d’examen correcte ne fournit ni priorité ni protocole clinique.
- **Validation de POC ≠ validation professionnelle** : les préférences source et une grille documentée permettent l'expérience scolaire ; elles ne prouvent pas l'aptitude à un usage clinique réel.
- **Détection PII ≠ anonymisation garantie** : un outil automatique a des faux positifs et des faux négatifs ; la revue et la gouvernance restent nécessaires.
- **Absence explicite ≠ donnée manquante à inventer** : le schéma `not_available` protège contre une extraction présentée à tort comme un fait source.

## Ce que nous savons maintenant

Le candidat SFT v2.1 est cohérent et reproductible pour ses contrôles techniques. Le schéma de métadonnées est testable. Les sources et licences sont traçables. La revue éducative du DPO existe, mais ses justifications et sa lignée doivent être consolidées ; la revue contextuelle PII reste ouverte. L'étape est donc partiellement terminée pour des raisons techniques, pas parce qu'un médecin fictif manquerait.

## Prochaine décision

Consolider la revue de POC du lot DPO et des références d'évaluation avec la grille du projet, puis avancer vers l'étape 2. Conserver `clinical_review_status: not_performed` pour signaler honnêtement l'absence de professionnel réel ; placer une véritable validation clinique dans la roadmap avant tout pilote hospitalier.
