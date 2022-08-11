# Codes CPV

Le CPV constitue un système de classification unique pour les marchés publics visant à standardiser les références utilisées pour décrire l'objet d'un marché par les pouvoirs adjudicateurs et les entités adjudicatrice.

L'utilisation des codes CPV est obligatoire dans l'Union Européenne à partir du 1er février 2006.

Version actuelle : 2008

## Listes des codes

http://www.cpv.enem.pl/fr

## Structure d'un code

Le vocabulaire principal repose sur une structure arborescente de codes comptant jusqu'à 9 chiffres auxquels correspond un intitulé qui décrit les fournitures, travaux ou services, objet du marché.

### Détails

- Les deux premiers chiffres servent à identifier les divisions (XX000000-Y)
- Les trois premiers chiffres servent à identifier les groupes (XXX00000-Y)
- Les quatre premiers chiffres servent à identifier les classes (XXXX0000-Y)
- Les cinq premiers chiffres servent à identifier les catégories (XXXXX000-Y)
- Un neuvième chiffre sert à la vérification des chiffres précédents

Si on ne prend en compte que les 8 premiers chiffres (en ignorant le chiffre de vérification), il y a 7 niveaux de hiérachie.

### Exemple

03000000-1 : Produits agricoles, de l'élevage, de la pêche, de la sylviculture et produits connexes

48814400-1 : Système d'information clinique

## Choix techniques

- nous stockons seulement les 8 premiers chiffres du code (le neuvième chiffre sert seulement de vérification, donc pas nécessaire)
