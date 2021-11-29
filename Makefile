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

