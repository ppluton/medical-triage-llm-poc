# Recherche du pilote CUDA : échec v31 et correction v32

Date : 2026-09-13 — Statut : draft

Source : journal Kaggle privé v31, SHA-256 `9f40537409185855341af463bca6e4688b50dc33c35861675a4827b3034798b8` ; runner `6f42e70`.

La CLI confirme ERROR. Les installations aboutissent, mais le contrôle ajouté dans v31 arrête le runner avec `Installed CUDA driver library not found in linker cache`. Le serveur vLLM n’a donc pas été lancé. Ce contrôle supposait à tort que le pilote accessible dans le conteneur apparaîtrait dans le cache ldconfig.

La correction v32 charge `libcuda.so.1` via le chargeur dynamique puis lit son chemin réel dans `/proc/self/maps`. Elle utilise ce fichier pour le lien local destiné au compilateur. Le pilote ne vient pas d’un téléchargement supplémentaire. Les erreurs de chargement ou de découverte restent bloquantes.

Validation locale : Ruff, génération/compilation du bootstrap et contrôle ciblé avec mappings simulés passent (résolution du lien, conservation de LIBRARY_PATH, rejet du pilote absent). Cela ne prouve pas le démarrage GPU ; v32 doit exécuter la même chaîne SFT/DPO → vLLM → API. Aucun entraînement ou résultat clinique ajouté.

## Contrôle Linux réel du mécanisme de découverte

Exécuté dans l’image locale `chsa-api:1f5693b`, avec `docker run --rm --network none`, runner monté en lecture seule. Une copie de `libm.so.6`, nommée `libcuda.so.1`, sert uniquement de bibliothèque témoin. Le sous-processus Python démarre avec son répertoire dans LD_LIBRARY_PATH ; le runner la charge réellement avec ctypes, retrouve son chemin dans `/proc/self/maps`, crée le lien attendu et préserve LIBRARY_PATH. Assertions réussies, sortie 0.

Le premier essai créait le répertoire après le démarrage de Python et le chargeur ne le trouvait pas ; le montage d’essai a été corrigé pour créer la bibliothèque avant le sous-processus. Aucun changement supplémentaire du runner n’était nécessaire. Ce contrôle prouve la découverte Linux d’une bibliothèque chargée, pas l’initialisation CUDA ou la compilation FlashInfer. Le conteneur temporaire est supprimé automatiquement après exécution.
