import environ

from config.sentry import sentry_init
from config.settings.base import *  # noqa


env = environ.Env()


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

SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", True)

MEDIA_URL = f"https://{S3_STORAGE_ENDPOINT_DOMAIN}/"  # noqa

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env.str("EMAIL_HOST")
EMAIL_PORT = env.str("EMAIL_PORT")
EMAIL_HOST_USER = env.str("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env.str("EMAIL_HOST_PASSWORD")


# Sentry
# ------------------------------------------------------------------------------

sentry_init(dsn=env.str("SENTRY_DSN_STAGING"))
