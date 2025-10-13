LINTER_CHECKED_DIRS := config lemarche scripts tests

# Global tasks.
# =============================================================================
PYTHON_VERSION := python3.13

.PHONY: shell_on_django_container shell_on_postgres_container
# DOCKER commands
# =============================================================================

# Django
shell_on_django_container:
	docker compose exec -ti app /bin/bash

# Postgres
shell_on_postgres_container:
	docker compose exec -ti db /bin/bash

# After migrate
populate_db:
	pg_restore -d marche --if-exists --clean --no-owner --no-privileges lemarche/perimeters/management/commands/data/perimeters_20220104.sql
	ls -d lemarche/fixtures/django/* | xargs django-admin loaddata
	django-admin create_content_pages

populate_db_container:
	docker compose exec -ti app bash -c "ls -d lemarche/fixtures/django/* | xargs django-admin loaddata"
	docker compose exec -ti app bash -c "django-admin create_content_pages"

# Tooling
# =============================================================================

quality:
	poetry run pflake8 $(LINTER_CHECKED_DIRS)
	poetry run isort $(LINTER_CHECKED_DIRS) --check-only
	poetry run black $(LINTER_CHECKED_DIRS) --check

fix:
	poetry run pflake8 $(LINTER_CHECKED_DIRS)
	poetry run isort $(LINTER_CHECKED_DIRS)
	poetry run black $(LINTER_CHECKED_DIRS)

clean:
	rm -r __pycache__/


# Deployment
# =============================================================================

deploy_prod: scripts/deploy_prod.sh
	./scripts/deploy_prod.sh

test_container:
	docker compose exec -ti app django-admin test --settings=config.settings.test --noinput --failfast --parallel auto $(TARGET)

test:
	django-admin test --settings=config.settings.test --noinput --failfast --parallel auto $(TARGET)

export_requirements:
	poetry export --without-hashes --output requirements/staging.txt
	poetry export --without-hashes --with dev --output requirements/dev.txt


