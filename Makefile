# Global tasks.
# =============================================================================
PYTHON_VERSION := python3.11

.PHONY: shell_on_django_container shell_on_django_container_as_root shell_on_postgres_container
# DOCKER commands
# =============================================================================

# Django
shell_on_django_container:
	docker compose exec -ti app /bin/bash

# Postgres
shell_on_postgres_container:
	docker compose exec -ti db /bin/bash

# Itou theme
update_itou_theme: scripts/upload_itou_theme.sh
	docker compose exec app /bin/sh -c "./scripts/upload_itou_theme.sh"

# After migrate
populate_db:
	pg_restore -d marche --if-exists --clean --no-owner --no-privileges lemarche/perimeters/management/commands/data/perimeters_20220104.sql
	ls -d lemarche/fixtures/django/* | xargs django-admin loaddata

populate_db_container:
	docker compose exec -ti app bash -c "ls -d lemarche/fixtures/django/* | xargs django-admin loaddata"

# Deployment
# =============================================================================

deploy_prod: scripts/deploy_prod.sh
	./scripts/deploy_prod.sh

test_container:
	docker compose exec -ti app django-admin test --settings=config.settings.test --noinput --failfast --parallel auto $(TARGET)

test:
	django-admin test --settings=config.settings.test --noinput --failfast --parallel auto $(TARGET)
