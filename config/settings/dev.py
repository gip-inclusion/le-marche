import os
import platform

from config.settings.base import *  # noqa


DEBUG = True

INSTALLED_APPS += ["django_extensions", "debug_toolbar"]  # noqa F405

MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]  # noqa F405

# For Docker env (and debug toolbar in particular)
import socket


_, _, ips = socket.gethostbyname_ex(socket.gethostname())
INTERNAL_IPS = [ip[: ip.rfind(".")] + ".1" for ip in ips] + ["127.0.0.1"]

# Authentication.
# ------------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = []  # Avoid password strength validation in DEV.


# Static files.
# ------------------------------------------------------------------------------

COMPRESS_ENABLED = False
COMPRESS_OFFLINE = False


# Emails.
# ------------------------------------------------------------------------------

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
# EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
# EMAIL_FILE_PATH = str(ROOT_DIR + "sent_emails")


# Security.
# ------------------------------------------------------------------------------

SESSION_COOKIE_SECURE = False

CSRF_COOKIE_SECURE = False


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

# see https://docs.python.org/3/library/platform.html#platform.win32_ver
is_windows = any(platform.win32_ver())

if is_windows:
    # Postgis Django needs GDAL
    # https://trac.osgeo.org/osgeo4w/
    GDAL_LIBRARY_PATH = "C:/OSGeo4W/bin/gdal304.dll"


# flake8: noqa F405
HUEY |= {
    "results": True,
    "store_none": True,
}  # Huey implementation to use.

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
