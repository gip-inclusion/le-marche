# Itou - Le marché de l'inclusion

> Le marché de l'inclusion est un service numérique permettant de trouver un prestataire sociale inclusif
> proposant des produits ou services professionnels.

## Définitions / nomenclature

Voici un tableau explicatif de la nomenclature utilisée dans le code (par rapport à l'application)

|Dans le métier               |Dans le code    |
|-----------------------------|----------------|
|Appel d'offres               |Tender          |
|Demande de devis             |Quote           |
|Sourcing                     |Project         |
|Liste de favoris             |Favorite list   |
|Structure                    |Siae            |
|Utilisateur                  |User            |
|Réseau                       |Network         |
|Demande de rattachement      |User request    |
|Prestation                   |Offer           |
|Référence client             |Client reference|
|Label & certification        |Label           |
|Secteur d'activité           |Sector          |
|Groupe de secteurs d'activité|Sector group    |
|Périmètre                    |Perimeter       |

## Installation

Étapes d'une installation en local à des fins de développement.
L'environnement fourni permet de fonctionner de deux manières différentes :

1. UV + Postgres (sans Docker)
2. Docker + Docker Compose (installe tout l'environnement nécessaire)

### UV (sans Docker)

#### Configuration

Pour un déploiement local **sans Docker**, dupliquez le fichier `env.default.sh` en `env.local.sh` et apportez-y les modifications nécessaires.

```bash
$ cp env.default.sh env.local.sh
# Préparation de l'environnement local
$ source ./env.local.sh
```

#### Installation & lancement

Prérequis :

- packets python à installer : uv
- initialiser une db Postgres (ne pas oublier l'extension PostGIS)

Installation et exécution :

```bash
# Installation environnement Python
$ uv sync

# Configuration environnement
$ source ./env.local.sh

# Activation de l'environnement virtuel
source .venv/bin/activate

# Exécution
$ ./manage.py runserver
$ ./manage.py [COMMANDES]
```

### Docker

Pour l'environnement de développement, un ficher `docker-compose.yml` est fourni et utilisable avec le plugin [Docker Compose](https://docs.docker.com/compose/).

Pour la configuration Django, vérifiez le fichier [config/settings/dev.py](./config/settings/dev.py).

#### Configuration Docker

Pour un déploiement local **avec Docker**, dupliquez le fichier `env.docker_default.local` en `env.docker.local` et apportez-y les modifications nécessaires (bien que la plupart des paramètres devraient fonctionner _hors de la boîte_).

#### Lancement Docker Compose

Après création du fichier `env.docker.local` :

```bash
 # Démarrage
 > docker compose up
 # Après démarrage, le serveur est disponible sur http://localhost:8880/

 # Se connecter au containeur django
 > docker compose exec -it app /bin/bash
 # ou
 > make shell_on_django_container

 # Re-création de l'environnement (en cas de modification)
 > docker compose down
 > docker compose build --no-cache
 > docker compose up --force-recreate

 # Effacement complet des images dockers
 > docker compose down -v
```

## Utilisation

Une fois lancé, l'application est disponible sur <http://localhost:8880/>.

Le dépôt de besoin utilise les périmètres. Il est possible de les charger avec les commandes Django :

```bash
./manage.py import_regions
./manage.py import_departements
./manage.py import_communes
```

### Données de test

```bash
make populate_db
```

> **Remarque** : `populate_db` exécute la commande `create_content_pages` qui crée 6 pages de types ContentPage :
('accessibilite', 'cgu', 'cgu-api', 'confidentialite', 'mentions-legales' et 'qui-sommes-nous').

## API

Il y a aussi une API, qui propose plusieurs endpoints et interfaces de documentation :

- Documentation Swaggger/OpenAPI : [/docs](http://localhost:8880/api/docs)
- Documentation ReDoc : [/redoc](http://localhost:8880/api/redoc)
- Schema OpenApi3 : [/redoc](http://localhost:8880/api/schema)

Tant que faire se peut, la documentation des endpoints se fait dans le code, en visant une bonne lisibilité
de la documentation autogénérée.

### Dépendances et environnement

Le projet centralise ses dépendances dans le fichier [pyproject.toml](pyproject.toml).
Uv utilise le fichier `uv.lock`

```bash
# Mise à jour dépendances
$ uv lock --upgrade
```

### Migrations

Si l'environnement est neuf ou n'est plus à jour, appliquez les migrations nécessaires :

```bash
# Avec manage.py
$ ./manage.py makemigrations
$ ./manage.py migrate
```

## Développement

Le repo suit le workflow [par branche de fonctionnalité](https://www.atlassian.com/fr/git/tutorials/comparing-workflows/feature-branch-workflow), et un [versionnage sémantique](CHANGELOG.md).

### Qualité du code

Mettre en place le `pre-commit` :

```bash
pre-commit install
```

Le projet utilise flake8, isort et black pour assurer la standardisation des écritures.

```bash
# Vérifier la qualité du code
$ make quality
# Exécuter formattage automatique
$ make fix
```

### Testing

PyTest & Selenium sont utilisés pour ce projet.
Les tests se trouvent dans les fichiers `tests.py` ou les répertoires [tests](tests) (un sous-répertoire par app django)

Pour lancer les tests :

```bash
./manage.py test
# pour lancer un lot de tests en particulier
./manage.py test -- lemarche.api.siaes.tests.SiaeListApiTest
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

## Serveur S3

En développement, normalement la configuration par défaut est suffisante.

Les variables du conteneur docker sont :

```
MINIO_ROOT_USER=minio_user
MINIO_ROOT_PASSWORD=minio_password
MINIO_BUCKET_NAME=bucket
```

et doivent correspondre aux variables des settings Django:

```
S3_STORAGE_ACCESS_KEY_ID = env.str("CELLAR_ADDON_KEY_ID", "minio_user")
S3_STORAGE_SECRET_ACCESS_KEY = env.str("CELLAR_ADDON_KEY_SECRET", "minio_password")
S3_STORAGE_ENDPOINT_DOMAIN = env.str("CELLAR_ADDON_HOST", "localhost:9000")
S3_STORAGE_BUCKET_NAME = env.str("S3_STORAGE_BUCKET_NAME", "bucket")
```

Pour accéder au portail du bucket: <http://localhost:9000/>
