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
$ env PYTHONPATH=./lemarche:./lemarche/c4_directory poetry run python manage.py [COMMANDES]
```

### Docker
L'API utilise un dockerfile multistage, permettant de fonctionner en "Dev" et "Prod" avec le même [Dockerfile](./Dockerfile).

#### Configuration docker

- Copier le fichier `env.default.sh` vers `env.docker.local`
- Supprimer les `export`
- Supprimer les guillements
- Completer les données

Format final de `env.docker.local` (exemple):
```
PG_HOST=localhost
PG_PORT=5432
PG_USER=db_user
```

#### Lancement
Le script [start_docker.sh](./start_docker.sh) permet de lancer les environnements en local, en mode **dev** ou **prod** :

```bash
 > ./start_docker.sh -h

-p|--prod    run full docker (Prod config)
-d|--dev     run dev docker (Dev config and local mounts)

# Pour lancer l'environnement de développement
> ./start_docker.sh --dev
```

## Utilisation
Une fois lancé, l'api propose plusieurs endpoints et interfaces de documentation (liens vers environnement local) :

- Documentation Swaggger/OpenAPI : [/docs](http://localhost:8000/docs)
- Documentation ReDoc : [/redoc](http://localhost:8000/redoc)
- Schema OpenApi3 : [/redoc](http://localhost:8000/schema)

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
Le repo suit le workflow [par branche de fonctionnalité](https://www.atlassian.com/fr/git/tutorials/comparing-workflows/feature-branch-workflow), 
et un [versionnage sémantique](CHANGELOG.md).

### Qualité du code
Le projet utilise flake8, isort et black pour assurer la standardisation des écritures.
Poetry est configuré pour en faciliter l'utilisation.

```bash
# Exécuter isort, flake8 ou black
$ poetry run poe black
$ poetry run poe isort
$ poetry run poe flake8
# Exécuter formattage automatique
$ poetry run poe clean
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

## Contenu de l'API du marché de l'inclusion
### Le projet aujourd'hui
- API du marché de l'inclusion, qui offre :
    - La liste des SIAE, leur données et secteurs d'activité
    - La liste hierarchisée des secteurs d'activité

### Le projet demain
En plus de l'API :
- Interface de consultation
- Moteur de recherche des structures
- Partenaires, consortiums, réseaux, ...
- Gestion des utilisateurs, des structures, ...
- Intégration de référentiels externes
- Pages d'info, thématiques, filières, ...
- Et bien d'autres choses ! 🛸
