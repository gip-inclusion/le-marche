[![Generic badge](https://img.shields.io/badge/ITOU-Oh_Oui-lightgreen.svg)](https://shields.io/)
[![Generic badge](https://img.shields.io/badge/État-En_Construction-yellow.svg)](https://shields.io/)
# Itou - le marché de l'inclusion - API
API du marché de l'inclusion

Publication de la liste de toutes les structures d'insertion et entreprises adaptées de France.

**Ce dépôt est en cours construction.**

## Données disponibles par structure
Pour une partie des structures, certaines donnéés peuvent manquer : leur meilleure qualification est un effort continu et soutenu.

- Nom
- Enseigne
- Siret
- Naf
- Site Web
- Adresse
- Localisation
- Date de création
- Nombre de salariés
- Types de prestation
- Type de la structure
- Secteurs d'activité

## Notes
Structure de l'API :

- `/list`
- `/search`
- ...

## Installation
Pâquets nécessaires à l'installation et l'exécution de l'API:
- Poetry
- python3-dev, default-libmysqlclient-dev

L'environnement se configure en copian `env.default.sh`

Installation et exécution:
```bash
> Installation environnement python
$ poetry install

> Configuration environnement
$ . env.local.sh

> Exécution 
$ poetry run python manage.py runserver
$ poetry run python manage.py [COMMANDES]

> Avec surcharge `PYTHONPATH` (à résoudre)
$ env PYTHONPATH=./itou_c4_api:./itou_c4_api/c4_directory poetry run python manage.py [COMMANDES]
```

### Ressources : 
- https://www.django-rest-framework.org/topics/rest-hypermedia-hateoas/
- https://realpython.com/django-rest-framework-quick-start/
- https://www.django-rest-framework.org/tutorial/5-relationships-and-hyperlinked-apis/
