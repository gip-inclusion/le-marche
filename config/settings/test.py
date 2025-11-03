import logging
import platform

from config.settings.base import *  # noqa


# Disable logging and traceback in unit tests for readability.
# https://docs.python.org/3/library/logging.html#logging.disable
logging.disable(logging.CRITICAL)

# Ensure Huey loggers are silenced in tests even if global logging is altered by unittest
# (use NullHandler and no propagation).
LOGGING["loggers"].update(
    {
        "huey": {"handlers": ["null"], "level": "CRITICAL", "propagate": False},
        "huey.consumer": {"handlers": ["null"], "level": "CRITICAL", "propagate": False},
    }
)

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

# Lower consumer noise if ever instantiated (should not in immediate mode during tests)
HUEY |= {
    "consumer": {
        "workers": 0,
        "worker_type": "thread",
        "loglevel": "critical",
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
        "LOCATION": "django_cache",
    }
}


# Nexus metabase db
# ---------------------------------------
NEXUS_METABASE_DB_HOST = DATABASES["default"]["HOST"]
NEXUS_METABASE_DB_PORT = DATABASES["default"]["PORT"]
NEXUS_METABASE_DB_DATABASE = DATABASES["default"]["NAME"]
NEXUS_METABASE_DB_USER = DATABASES["default"]["USER"]
NEXUS_METABASE_DB_PASSWORD = DATABASES["default"]["PASSWORD"]
