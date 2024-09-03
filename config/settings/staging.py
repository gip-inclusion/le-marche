import environ

from .base import *  # noqa
from .sentry import sentry_init


env = environ.Env()


STORAGES = {
    "default": {
        # "BACKEND": "storages.backends.s3.S3Storage",
        "BACKEND": "lemarche.utils.s3boto.S3BotoStorage",
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


ALLOWED_HOSTS = [
    "127.0.0.1",
    "staging.inclusion.beta.gouv.fr",
    "staging.lemarche.inclusion.beta.gouv.fr",
    "bitoubi-django-staging.cleverapps.io",
    # for review apps
    ".cleverapps.io",
]
CSRF_TRUSTED_ORIGINS = [
    "https://*.inclusion.beta.gouv.fr",
    "https://bitoubi-django-staging.cleverapps.io",
    "https://*.cleverapps.io",
]

SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", True)

MEDIA_URL = f"https://{S3_STORAGE_ENDPOINT_DOMAIN}/"  # noqa


# Sentry
# ------------------------------------------------------------------------------

sentry_init(dsn=env.str("SENTRY_DSN_STAGING"))
