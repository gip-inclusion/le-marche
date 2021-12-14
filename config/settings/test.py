import logging
import platform

from .base import *  # noqa


# Disable logging and traceback in unit tests for readability.
# https://docs.python.org/3/library/logging.html#logging.disable
logging.disable(logging.CRITICAL)

# `ManifestStaticFilesStorage` (used in base settings) requires `collectstatic` to be run.
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
COMPRESS_OFFLINE = False

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# see https://docs.python.org/3/library/platform.html#platform.win32_ver
is_windows = any(platform.win32_ver())

if is_windows:
    # Postgis Django needs GDAL
    # https://trac.osgeo.org/osgeo4w/
    GDAL_LIBRARY_PATH = "C:/OSGeo4W/bin/gdal304.dll"
