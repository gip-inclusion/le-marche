import environ

from .base import *  # noqa
from .sentry import sentry_init


env = environ.Env()


ALLOWED_HOSTS = [
    "inclusion.beta.gouv.fr",
    "lemarche.inclusion.beta.gouv.fr",
    "api.lemarche.inclusion.beta.gouv.fr",
    "bitoubi-django.cleverapps.io",
]

CSRF_TRUSTED_ORIGINS = [
    "https://lemarche.inclusion.beta.gouv.fr",
]

SECURE_SSL_REDIRECT = env.str("SECURE_SSL_REDIRECT", True)

MEDIA_URL = f"https://{S3_STORAGE_ENDPOINT_DOMAIN}/"  # noqa

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "bucket_name": S3_STORAGE_BUCKET_NAME,  # noqa
            "access_key": S3_STORAGE_ACCESS_KEY_ID,  # noqa
            "secret_key": S3_STORAGE_SECRET_ACCESS_KEY,  # noqa
            "endpoint_url": f"https://{S3_STORAGE_ENDPOINT_DOMAIN}",  # noqa
            "region_name": S3_STORAGE_BUCKET_REGION,  # noqa
            "file_overwrite": False,
            "location": env.str("S3_LOCATION", ""),
        },
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}


# Sentry
# ------------------------------------------------------------------------------

sentry_init(dsn=env.str("SENTRY_DSN_PROD"))


# Active Elastic APM metrics
# See https://www.elastic.co/guide/en/apm/agent/python/current/configuration.html
# ------------------------------------------------------------------------------

INSTALLED_APPS += ["elasticapm.contrib.django"]  # noqa F405
MIDDLEWARE += ["elasticapm.contrib.django.middleware.TracingMiddleware"]  # noqa

ELASTIC_APM = {
    "ENABLED": env.bool("APM_ENABLED", True),
    "SERVICE_NAME": "marche-django",
    "SERVICE_VERSION": env.str("COMMIT_ID", None),
    "SERVER_URL": env.str("APM_SERVER_URL", ""),
    "SECRET_TOKEN": env.str("APM_AUTH_TOKEN", ""),
    "ENVIRONMENT": BITOUBI_ENV,  # noqa
    "DJANGO_TRANSACTION_NAME_FROM_ROUTE": True,
    "TRANSACTION_SAMPLE_RATE": 0.1,
}
