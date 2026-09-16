# Reprise SFT seule de la réserve — Kaggle v46

- Date : 2026-09-16
- Statut observé : `QUEUED`
- Notebook privé : `pierrepluton/chsa-source-sft-qwen3`, version 46
- Candidat : SFT v39, étape 150
- Notebook SHA-256 : `d812ff715272aba50f91480b789c69c1f55156c02ae95da1ee4eb12abd5153a0`
- Optimisation : 0 étape

La v46 retire du run final le dataset et la vérification DPO inutiles. Le package monte
exactement deux ressources privées : le snapshot Base et le SFT v39 sélectionné. Le préflight
décompresse 21 fichiers, confirme la décision SFT, le checksum du notebook, l’appel au
vérificateur Base, le contrôle de réserve relocalisable et l’absence d’une variable DPO active
dans le bootstrap.

Les v44 et v45 ont toutes deux échoué avant chargement du modèle et avant génération. La v46
ne modifie ni sélection, ni poids, ni prompt, ni garde-fou ; elle supprime seulement une
dépendance d’un candidat non sélectionné. Son statut `QUEUED` n’est pas encore une preuve
d’exécution.
