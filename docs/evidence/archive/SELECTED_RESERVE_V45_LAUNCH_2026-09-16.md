# Reprise technique de la réserve sélectionnée — Kaggle v45

- Date : 2026-09-16
- Statut observé : `QUEUED`
- Notebook privé : `pierrepluton/chsa-source-sft-qwen3`, version 45
- Candidat inchangé : SFT v39, étape 150
- Notebook SHA-256 : `26b41bf1a963953267413c5d32ab1df78b41f1974fed20dd96e2bbc731ea0972`
- Optimisation : 0 étape

La v45 corrige uniquement la comparaison des chemins de fichiers du manifeste gelé. Le
préflight local décompresse les 21 fichiers réellement embarqués et vérifie : décision SFT,
contrôle `verify_base_snapshot`, absence de dépendance à un ancien notebook, trois datasets
privés exacts et nouveau contrôle de manifeste indépendant de l’emplacement.

La v44 a lu la réserve pour recalculer ses hashes puis a échoué avant chargement du modèle et
avant toute génération. La v45 est donc une reprise technique du même protocole et non une
nouvelle sélection motivée par des résultats de réserve. Son statut `QUEUED` ne prouve encore
aucune exécution.
