import os

from .base import *  # noqa


LOADED_SETTINGS = "dev"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 4}},
]

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    os.environ.get("CURRENT_HOST"),
]
