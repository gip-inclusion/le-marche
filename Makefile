# Global tasks.
# =============================================================================
PYTHON_VERSION := python3.9

.PHONY: shell_on_django_container shell_on_django_container_as_root shell_on_postgres_container
# DOCKER commands
# =============================================================================

# Django
shell_on_django_container:
	docker exec -ti bitoubi_django /bin/bash

shell_on_django_container_as_root:
	docker exec -ti --user root bitoubi_django /bin/bash

# Postgres
shell_on_postgres_container:
	docker exec -ti bitoubi_postgres /bin/bash

# Itou theme
update_itou_theme: scripts/upload_itou_theme.sh
	docker exec bitoubi_django /bin/sh -c "./scripts/upload_itou_theme.sh"


# Deployment
# =============================================================================

deploy_prod: scripts/deploy_prod.sh
	./scripts/deploy_prod.sh

test_container:
	docker exec -ti bitoubi_django django-admin test --settings=config.settings.test $(TARGET) --noinput --failfast --parallel

test:
	django-admin test --settings=config.settings.test $(TARGET) --noinput --failfast --parallel
