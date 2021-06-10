[![Generic badge](https://img.shields.io/badge/ITOU-Oh_Oui-lightgreen.svg)](https://shields.io/)
[![Generic badge](https://img.shields.io/badge/État-En_Construction-yellow.svg)](https://shields.io/)
# Itou - le marché de l'inclusion - API
API du marché de l'inclusion

Publication de la liste de toutes les structures d'insertion et entreprises adaptées de France.

**Ce dépôt est en cours de construction.**

## Installation
Étapes d'une installation en local à des fins de développement.

### Configuration
Les variables d'environnement sont listées dans le fichier [env.default.sh](env.default.sh).

Pour un déploiement local hors docker, renommez le fichier en `env.local.sh` et apportez-y les modifications nécessaires.
```bash
$ cp env.default.sh env.local.sh
# Préparation de l'environnement local
$ . env.local.sh
```

### Poetry
Paquets nécessaires à l'installation et l'exécution de l'API:
- Poetry
- python3-dev, default-libmysqlclient-dev

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

### Dépendances et environnement
Tant que faire ce peut, le projet centralise ses dépendances dans le fichier [pyproject.toml](pyproject.toml).
Poetry utilise le fichier `poetry.lock`, et génère également un fichier `requirements.txt`.

(c'est ce choix qui motive l'utilisation de `pflake8` et `poethepoet`).

```bash
# Mise à jour dépendances
$ poetry update
# Mise à jour requirements.txt
$ poetry run poe export
```

### Migrations
Si l'environnement est neuf ou n'est plus à jour, appliquez les migrations nécessaires

```bash
$ poetry run python manage.py migrate
```

## Développement
Le repo suit le workflow [par branche de fonctionnalité](https://www.atlassian.com/fr/git/tutorials/comparing-workflows/feature-branch-workflow), 
et un [versionnage sémantique](CHANGELOG.md).

### Qualité du code
Le projet utilise flake8, isort et black pour assurer la standardisation des écritures.
Poetry est configuré pour en faciliter l'utilisation.



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
### Ressources : 
- https://www.django-rest-framework.org/topics/rest-hypermedia-hateoas/
- https://realpython.com/django-rest-framework-quick-start/
- https://www.django-rest-framework.org/tutorial/5-relationships-and-hyperlinked-apis/
