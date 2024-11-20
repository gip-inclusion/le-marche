# Global tasks.
# =============================================================================
PYTHON_VERSION := python3.11

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
	djan-admin create_content_pages

populate_db_container:
	docker compose exec -ti app bash -c "ls -d lemarche/fixtures/django/* | xargs django-admin loaddata"
	docker compose exec -ti app bash -c "django-admin create_content_pages"

# Deployment
# =============================================================================

deploy_prod: scripts/deploy_prod.sh
	./scripts/deploy_prod.sh

test_container:
	docker compose exec -ti app django-admin test --settings=config.settings.test --noinput --failfast --parallel auto $(TARGET)

test:
	django-admin test --settings=config.settings.test --noinput --failfast --parallel auto $(TARGET)
