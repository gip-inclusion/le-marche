import environ

from ._sentry import sentry_init
from .base import *  # noqa


env = environ.Env()


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
DEFAULT_FILE_STORAGE = "lemarche.utils.s3boto.S3BotoStorage"


# Sentry.
# ------------------------------------------------------------------------------

sentry_init(dsn=env.str("SENTRY_DSN_STAGING"))
