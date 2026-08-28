# Acquisition contrôlée — FrenchMedMCQA

- **Statut :** partially_proven
- **Révision :** `be9a03fde01d9f05107b14941af1ad99897691cf`
- **Artefact :** `DEFT-2023-FULL.zip`, hors Git

La récupération a produit un fichier de 550 466 octets avec le SHA-256 `58724ce1ac97b01b89ad5a6d4d1d9b9de3379d36feaaa11058d88aad8a2af4c9`. `unzip -t` a terminé sans erreur.

Le manifeste est `candidate`. Provenance, licence affichée et intégrité d'archive sont vérifiées. L'archive contient 2 171 exemples `train`, 312 `dev` et 622 `test`, sans chevauchement d'identifiants. Un scan regex n'a trouvé ni email ni numéro de téléphone français standard. Les contrôles PII Presidio, revue manuelle et fuite sémantique restent requis ; aucun exemple ne doit donc servir à la baseline, au SFT, au DPO ou à l'évaluation.
