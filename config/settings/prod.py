import environ

from config.sentry import sentry_init
from config.settings.base import *  # noqa


env = environ.Env()

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
        "BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage",
    },
}

# Database
# ------------------------------------------------------------------------------

DATABASES["stats"] = {  # noqa: F405
    "ENGINE": "django.db.backends.postgresql",
    "HOST": env.str("STATS_POSTGRESQL_ADDON_HOST", "localhost"),
    "PORT": env.str("STATS_POSTGRESQL_ADDON_PORT", "5432"),
    "NAME": env.str("STATS_POSTGRESQL_ADDON_DB", "marchetracker"),
    "USER": env.str("STATS_POSTGRESQL_ADDON_USER", "itou"),
    "PASSWORD": env.str("STATS_POSTGRESQL_ADDON_PASSWORD", "password"),
}
DATABASE_ROUTERS = ["config.stats_router.StatsRouter"]

# Sentry
# ------------------------------------------------------------------------------

sentry_init(dsn=env.str("SENTRY_DSN_PROD"))

# Logging
# ------------------------------------------------------------------------------

# json formatter for Datadog
LOGGING["handlers"]["console"]["formatter"] = "json"  # noqa: F405
