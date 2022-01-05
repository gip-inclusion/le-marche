import environ

from ._sentry import sentry_init
from .base import *  # noqa


env = environ.Env()


ALLOWED_HOSTS = [
    "inclusion.beta.gouv.fr",
    "lemarche.inclusion.beta.gouv.fr",
    "api.lemarche.inclusion.beta.gouv.fr",
    "bitoubi-django.cleverapps.io",
]


# Sentry.
# ------------------------------------------------------------------------------

sentry_init(dsn=env.str("SENTRY_DSN_PROD"))

SECURE_SSL_REDIRECT = env.str("SECURE_SSL_REDIRECT", True)
