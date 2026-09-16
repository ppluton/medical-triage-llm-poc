# Réancrer les préférences après une transformation du SFT

- Date : 2026-09-16
- Statut : draft
- Sources : manifeste SFT v2.2, manifeste DPO v2 et preuve de réancrage DPO v3.

Une anonymisation peut conserver les splits et le sens général d'un corpus tout en
changeant ses octets et les empreintes de certains prompts. Le simple fait que le
jeu DPO n'ait pas changé ne suffit donc pas : sa preuve d'absence de recouvrement
doit être recalculée contre la version réellement utilisée par le nouveau SFT.

Ici, les réponses préférées et rejetées n'ont pas été réécrites. Le changement porte
uniquement sur la gouvernance : le manifeste DPO v3 protège toutes les instructions
du canonique SFT v2.2 et prouve à nouveau un recouvrement nul. Cela évite de confondre
« mêmes données DPO » avec « lignée encore valide ».

À retenir : après toute transformation de texte en amont, même limitée à quelques
masques, recalculer les empreintes d'isolation et lier la décision aux checksums
courants avant de lancer l'entraînement suivant.
