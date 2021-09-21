import os

from .base import *  # noqa

DEBUG = True

INSTALLED_APPS += ["django_extensions", "debug_toolbar"]  # noqa F405

MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]  # noqa F405

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 4}},
]

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    os.environ.get("CURRENT_HOST"),
]

INTERNAL_IPS = [
    "127.0.0.1",
]


# django-extensions settings.
# https://django-extensions.readthedocs.io/en/latest/index.html
# ----------------------------------------------------
SHELL_PLUS = "ipython"
SHELL_PLUS_IMPORTS = [
    "import csv, json, yaml",
    "from datetime import datetime, date, timedelta",
]

# django-debug-toolbar settings.
# https://django-debug-toolbar.readthedocs.io/en/latest/
# ----------------------------------------------------
DEBUG_TOOLBAR_CONFIG = {
    # https://django-debug-toolbar.readthedocs.io/en/latest/panels.html#panels
    "DISABLE_PANELS": [
        "debug_toolbar.panels.redirects.RedirectsPanel",
        # ProfilingPanel makes the django admin extremely slow...
        "debug_toolbar.panels.profiling.ProfilingPanel",
    ],
    "SHOW_TEMPLATE_CONTEXT": True,
}
