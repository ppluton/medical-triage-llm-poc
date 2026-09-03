# Preuve de génération SFT expérimentale 5 000

- **Date :** 2026-09-03
- **Statut :** proven for educational dataset generation; not clinically validated
- **Code :** `77ff443`
- **Run :** `educational-sft-v1-2026-09-03`

## Claim vérifié

Le générateur produit 5 000 enregistrements synthétiques conformes au contrat, avec les splits exacts 4 000/500/500, sans doublon exact de contenu, sans fuite de groupe bilingue et sans validation clinique déclarée.

## Résultats

- 5 000 lignes : 2 500 FR et 2 500 EN ;
- 4 000 train, 500 validation, 500 test ;
- 1 826 `maximum`, 2 254 `moderate`, 920 `deferred` ;
- neuf familles tracées dans chaque ligne ;
- 0 doublon exact contexte+cible ;
- 0 groupe bilingue réparti sur plusieurs splits ;
- 0 cas `insufficient_information` classé `deferred` ;
- 5 000 statuts cliniques `pending`.

## Échecs observés et corrections

1. Première génération : 168 doublons exacts mesurés.
2. Après variations d'antécédents, traitements et allergies : 4 doublons ; run refusé par le nouveau garde-fou.
3. Après variation temporelle déterministe : 0 doublon ; génération acceptée.

## Intégrité

- dataset canonique : `68aaec6ef463cb40f2ce7477fc5d04a7076c5f5163040efa49946e91fd122f30` ;
- train Qwen3, 4 000 lignes : `bd359751cccfa7e18a410cbcd000172723511cf76bf523b5df35c8839966e62f` ;
- validation Qwen3, 500 lignes : `f43e1b613830c94227d4db2a5ecfe25335a3b0efb86605bc3ca24e6f34df5014` ;
- protocole : `87b811278459ce6a299481afac71188815e9bc5b6f4265a334b893efbdc39c97` ;
- file candidate : `e4ac60c336aeb24dfb602f8e6f4539217f6f751239ac321946322a9ff68bdd9d`.

## Frontière de preuve

**Prouvé :** génération, schémas, distributions, unicité exacte, isolation des groupes, traçabilité et préparation Qwen3 train/validation.

**Non prouvé :** pertinence clinique des cibles, diversité sémantique suffisante, apprentissage réussi, amélioration par rapport au modèle Base, qualité DPO ou comportement de l'API.
