import logging
import platform

from .base import *  # noqa


# Disable logging and traceback in unit tests for readability.
# https://docs.python.org/3/library/logging.html#logging.disable
logging.disable(logging.CRITICAL)

# Static files are not compressed in test environment
COMPRESS_OFFLINE = False

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

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
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
        "LOCATION": "django_cache",
    }
}
