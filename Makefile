LINTER_CHECKED_DIRS := config lemarche scripts tests

# Global tasks.
# =============================================================================
PYTHON_VERSION := python3.13

USE_VENV := $(shell test -d .venv && echo 'TRUE')
ifeq "$(USE_VENV)" "TRUE"
	ENV_SHELL_PREFIX :=
else
	ENV_SHELL_PREFIX := docker compose exec -ti app
endif

# DOCKER commands
# =============================================================================
.PHONY: shell_on_django_container shell_on_postgres_container load_fixtures populate_db populate_db_container

# Django
shell_on_django_container:
	docker compose exec -ti app /bin/bash

# Postgres
shell_on_postgres_container:
	docker compose exec -ti db /bin/bash

# After migrate
load_fixtures:
	ls -d lemarche/fixtures/django/* | xargs ./manage.py loaddata

populate_db: load_fixtures
	pg_restore -d marche --if-exists --clean --no-owner --no-privileges lemarche/perimeters/management/commands/data/perimeters_20220104.sql
	./manage.py create_content_pages

populate_db_container:
	docker compose exec -ti app bash -c "ls -d lemarche/fixtures/django/* | xargs django-admin loaddata"
	docker compose exec -ti app bash -c "django-admin create_content_pages"

# Tooling
# =============================================================================
.PHONY: quality fix clean

quality:
	$(ENV_SHELL_PREFIX) ruff format --check $(LINTER_CHECKED_DIRS)
	$(ENV_SHELL_PREFIX) ruff check $(LINTER_CHECKED_DIRS)
	$(ENV_SHELL_PREFIX) python manage.py makemigrations --check --dry-run --noinput || (echo "⚠ missing migration ⚠"; exit 1)

fix:
	$(ENV_SHELL_PREFIX) ruff format $(LINTER_CHECKED_DIRS)
	$(ENV_SHELL_PREFIX) ruff check --fix $(LINTER_CHECKED_DIRS)

clean:
	rm -r __pycache__/


# Deployment
# =============================================================================
.PHONY: deploy_prod test

deploy_prod: scripts/deploy_prod.sh
	./scripts/deploy_prod.sh

test:
	$(ENV_SHELL_PREFIX) pytest --numprocesses=logical --create-db




