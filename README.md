# Itou - Le marché de l'inclusion

> Le marché de l'inclusion est un service numérique permettant de trouver un prestataire sociale inclusif
> proposant des produits ou services professionnels.

## Installation

Étapes d'une installation en local à des fins de développement.
L'environnement fourni permet de fonctionner de 3 manières différentes :

1. Poetry + Postgres (sans Docker)
2. Dockerfile + Postgres
3. docker-compose (installe tout l'environnement nécessaire)

### Poetry (sans Docker)

#### Configuration

Pour un déploiement local **sans Docker**, dupliquez le fichier `env.default.sh` en `env.local.sh` et apportez-y les modifications nécessaires.

```bash
$ cp env.default.sh env.local.sh
# Préparation de l'environnement local
$ source ./env.local.sh
```

#### Installation & lancement

Prérequis :
- packets python à installer : poetry, python3.9, python3.9-dev, default-libmysqlclient-dev
- initialiser une db Postgres (ne pas oublier l'extension PostGIS)

Installation et exécution :

```bash
> Installation environnement Python
$ poetry install

> Configuration environnement
$ source ./env.local.sh

> Exécution
$ poetry run python manage.py runserver
$ poetry run python manage.py [COMMANDES]

> Avec surcharge `PYTHONPATH` (à résoudre)
$ env PYTHONPATH=./lemarche:./lemarche/c4_directory poetry run python manage.py [COMMANDES]
```

### Docker

L'application utilise un Dockerfile multistage, permettant de fonctionner en "Dev" et "Prod" avec le même [Dockerfile](./Dockerfile).

Pour l'environnement de développement, un `docker-compose` est fourni (voir ci-dessous).

Pour la configuration Django, vérifiez le fichier [config/settings/dev.py](./config/settings/dev.py).

#### Configuration Docker

Pour un déploiement local **avec Docker**, dupliquez le fichier `env.docker_default.local` en `env.docker.local` et apportez-y les modifications nécessaires (bien que la plupart des paramètres devraient fonctionner _hors de la boîte_).

> :information_source: pour accéder à l'environnemnt depuis une autre machine, pensez à définir la variable d'environnemnt `CURRENT_HOST` dans le fichier d'environnement

#### Lancement docker-compose

Après création du fichier `env.docker.local` :

```bash
 # Démarrage
 > docker-compose up
 # Après démarrage, le serveur est disponible sur http://localhost:8880/

 # Se connecter au containeur django
 > docker exec -it bitoubi_django /bin/bash
 # ou
 > make shell_on_django_container

 # Re-création de l'environnement (en cas de modification)
 > docker-compose down
 > docker-compose build --no-cache
 > docker-compose up --force-recreate

 # Effacement complet des images dockers
 > ./scripts/delete_docker.sh

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
# Mise à jour requirements/staging.txt
$ poetry run poe export
# Mise à jour requirements/dev.txt
$ poetry run poe export_dev
```

### Migrations

Si l'environnement est neuf ou n'est plus à jour, appliquez les migrations nécessaires :

```bash
# Avec manage.py
$ poetry run python manage.py makemigrations
$ poetry run python manage.py migrate
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

PyTest & Selenium sont utilisés pour ce projet.
Les tests se trouvent dans les fichiers `tests.py` ou les répertoires [tests](tests) (un sous-répertoire par app django)

Pour lancer les tests :

```bash
poetry run python manage.py test
# pour lancer un lot de tests en particulier
poetry run python manage.py test -- lemarche.api.siaes.tests.SiaeListApiTest
```

## Taches asynchrones
### Setup
#### Huey storage mode
Mode direct (sans task queue) :
```
export CONNECTION_MODE_TASKS="direct"
```

Mode redis :
```
export CONNECTION_MODE_TASKS="redis"
```
Mode sqlite :
```
export CONNECTION_MODE_TASKS="sqlite"
```

Mode redis :
```
export CONNECTION_MODE_TASKS="redis"
```
#### Lancer en local
1/ Lancer un serveur local
2/ Dans un autre shell lancer la commande
```
/manage.py run_huey
```

#### Lancer sur CleverCloud
Ajouter la variable d'environnement suivante sur la config clever cloud :

```
CC_WORKER_COMMAND=django-admin run_huey
```