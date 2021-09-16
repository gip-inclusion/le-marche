import environ

from .base import *  # noqa


env = environ.Env()


DEBUG = False

ALLOWED_HOSTS = [
    env.str("CURRENT_HOST"),
]

COMPRESS_STORAGE = (
    "compressor.storage.GzipCompressorFileStorage"  # Instead of pre-set "storages.backends.s3boto3.S3Boto3Storage"
)
COMPRESS_ROOT = STATIC_ROOT  # noqa
COMPRESS_OFFLINE = True  # Needed to run compress offline

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 4}},
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]
