# Global tasks.
# =============================================================================
PYTHON_VERSION := python3.9

.PHONY: shell_on_django_container shell_on_django_container_as_root shell_on_postgres_container

shell_on_django_container:
	docker exec -ti bitoubi_django /bin/bash

shell_on_django_container_as_root:
	docker exec -ti --user root bitoubi_django /bin/bash

shell_on_postgres_container:
	docker exec -ti bitoubi_postgres /bin/bash


# Itou theme
# =============================================================================

update_itou_theme: scripts/upload_itou_theme.sh
	docker exec bitoubi_django /bin/sh -c "./scripts/upload_itou_theme.sh"
