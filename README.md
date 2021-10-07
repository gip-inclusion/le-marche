[![Generic badge](https://img.shields.io/badge/ITOU-Oh_Oui-lightgreen.svg)](https://shields.io/)
[![Generic badge](https://img.shields.io/badge/État-En_Construction-yellow.svg)](https://shields.io/)

# Itou - Le marché de l'inclusion

> Le marché de l'inclusion est un service numérique permettant de trouver un prestataire sociale inclusif
> proposant des produits ou services professionnels.

**Ce dépôt est en cours de construction.**

## Installation

Étapes d'une installation en local à des fins de développement.
L'environnement fourni permet de fonctionner de 3 manières différentes:

1. Poetry (et Postgres existant)
2. Dockerfile (et Postgres existant)
3. docker-compose (installe tout l'environnement nécessaire)

### Configuration

Les variables d'environnement sont listées dans le fichier [env.default.sh](env.default.sh).

Pour un déploiement local **hors docker**, renommez le fichier en `env.local.sh` et apportez-y les modifications nécessaires.
```bash
$ cp env.default.sh env.local.sh
# Préparation de l'environnement local
$ source ./env.local.sh
```

Pour un déploiement local **sous docker**, renommez le fichier `env.docker_default.local` en `env.docker.local` et apportez-y les modifications nécessaires (bien que la plupart des paramètres devraient fonctionner _hors de la boîte_).

> :information_source: **Accès données MySQL** : L'api lit les données de la BD du marché [itou-cocorico](https://github.com/betagouv/itou-cocorico/). Pour pouvoir fonctionner pleinement en local, cela signifie que le marché doit tourner également en local (le fichier de configuration [env.docker_default.local](./env.docker_default.local) est d'ailleurs prévu à cet effet).

### Poetry

Prérequis :
- packets python à installer : poetry, python3.9, python3.9-dev, default-libmysqlclient-dev
- initialiser une db Postgres pour pour itou-marche-api (ne pas oublier l'extension PostGIS)
- avoir une db MariaDB qui tourne (voir itou-cocorico)

Installation et exécution :
```bash
> Installation environnement python
$ poetry install

> Configuration environnement
$ source ./env.local.sh

> Exécution 
$ poetry run python manage.py runserver
$ poetry run python manage.py [COMMANDES]

> Avec surcharge `PYTHONPATH` (à résoudre)
$ env PYTHONPATH=./lemarche:./lemarche/c4_directory poetry run python manage.py [COMMANDES]

> Avoir le MariaDB de itou-cocorico qui tourne
```

### Docker

L'API utilise un dockerfile multistage, permettant de fonctionner en "Dev" et "Prod" avec le même [Dockerfile](./Dockerfile).

Pour l'environnement de développement, un `docker-compose` est fourni (voir ci-dessous).

Pour la configuration django, vérifiez le fichier (config/settings/dev.py)[./config/settings/dev.py].

#### Configuration Docker

Pour un déploiement local **sous Docker**, renommez le fichier `env.docker_default.local` en `env.docker.local` et apportez-y les modifications nécessaires (bien que la plupart des paramètres devraient fonctionner _hors de la boîte_).

> :information_source: pour accéder à l'environnemnt depuis une autre machine, pensez à définir la variable d'environnemnt `CURRENT_HOST` dans le fichier d'environnement


#### Lancement docker-compose

Après création du fichier `env.docker.local`,

```bash
 # Démarrage
 > docker-compose up
 # Après démarrage, le serveur est disponible sur http://localhost:8880/

 # Se connecter au containeur django
 > docker exec -it bitoubi_django /bin/bash

 # Re-création de l'environnement (en cas de modification)
 > docker-compose down
 > docker-compose build --no-cache
 > docker-compose up --force-recreate    
```

#### Lancement Dockerfile

Le script [start_docker.sh](./start_docker.sh) permet de lancer les environnements en local, en mode **dev** ou **prod** :

```bash
 > ./start_docker.sh -h

-p|--prod    run full docker (Prod config)
-d|--dev     run dev docker (Dev config and local mounts)

# Pour lancer l'environnement de développement
> ./start_docker.sh --dev
```

## Utilisation

Une fois lancé, l'application est disponible sur http://localhost:8880/.

## API

Il y a aussi une API, qui propose plusieurs endpoints et interfaces de documentation :

- Documentation Swaggger/OpenAPI : [/docs](http://localhost:8880/api/docs)
- Documentation ReDoc : [/redoc](http://localhost:8880/api/redoc)
- Schema OpenApi3 : [/redoc](http://localhost:8880/api/schema)

Tant que faire se peut, la documentation des endpoints se fait dans le code, en visant une bonne lisibilité
de la documentation autogénérée.

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
# Avec manage.py
$ poetry run python manage.py makemigrations
$ poetry run python manage.py migrate
# Avec poe, dans le shell poetry (ou directement dans le docker - poe, pas poetry)
$ poetry shell
$ poe makemigrations
$ poe migrate
```

## Développement

Le repo suit le workflow [par branche de fonctionnalité](https://www.atlassian.com/fr/git/tutorials/comparing-workflows/feature-branch-workflow), et un [versionnage sémantique](CHANGELOG.md).

### Qualité du code

Le projet utilise flake8, isort et black pour assurer la standardisation des écritures.
Poetry est configuré pour en faciliter l'utilisation.

```bash
# Exécuter isort, flake8 ou black, avec poetry
$ poetry run poe black
$ poetry run poe isort
$ poetry run poe flake8
# Exécuter formattage automatique
$ poetry run poe clean_code

# Exécuter formattage automatique dans le docker
$ poe clean_code
```

### Testing

PyTest est utilisé pour ce projet. Les tests se trouvent dans le répertoire [tests](tests),
un sous-répertoire par app django.

### TODO List

- Dockerfile pour développement
- Logging
- Monitoring
- Tracking

### Ressources et inspirations

- https://www.django-rest-framework.org/topics/rest-hypermedia-hateoas/
- https://realpython.com/django-rest-framework-quick-start/
- https://www.django-rest-framework.org/tutorial/5-relationships-and-hyperlinked-apis/
- https://github.com/wsvincent/awesome-django
- https://dev.to/sherlockcodes/pytest-with-django-rest-framework-from-zero-to-hero-8c4
- https://hannylicious.com/blog/testing-django/
- https://flowfx.de/blog/populate-your-django-test-database-with-pytest-fixtures/
