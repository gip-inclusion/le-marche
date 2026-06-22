"""Restore data-migration-seeded rows wiped by transactional flushes.

There is no ``serialized_rollback`` configured, so when a
``TransactionTestCase``/``transactional_db`` test flushes its worker database at
teardown, rows created by data migrations (Wagtail root page + locale,
``EmailGroup``, ``TemplateTransactional``, ...) are truncated and never restored.

Django normally avoids the fallout by running every ``TestCase`` before every
``TransactionTestCase``, but ``pytest-randomly`` shuffles across that boundary
(and xdist distributes per worker), so on some seeds a flushing test runs before
data-dependent ones on the same worker and they hit empty tables.

We snapshot those rows once per worker (``dumpdata`` with natural foreign keys so
``content_type`` references survive the content types that ``post_migrate``
re-creates with new PKs after a flush) and reload them before any DB test that
finds them wiped.
"""

import pytest


_RESEED_MODELS = [
    "wagtailcore.locale",
    "wagtailcore.collection",
    "wagtailcore.page",
    "wagtailcore.site",
    "conversations.emailgroup",
    "conversations.templatetransactional",
]

_snapshot = {}


@pytest.fixture(scope="session", autouse=True)
def _capture_seed_snapshot(django_db_setup, django_db_blocker, tmp_path_factory):
    from django.core.management import call_command

    path = str(tmp_path_factory.mktemp("seed") / "seed.json")
    with django_db_blocker.unblock(), open(path, "w") as fh:
        call_command("dumpdata", *_RESEED_MODELS, natural_foreign=True, stdout=fh)
    _snapshot["path"] = path
    _snapshot["blocker"] = django_db_blocker


def _uses_db(item):
    from django.test import TransactionTestCase

    cls = getattr(item, "cls", None)
    if cls is not None:
        return issubclass(cls, TransactionTestCase)
    names = getattr(item, "fixturenames", ())
    return "db" in names or "transactional_db" in names


def pytest_runtest_setup(item):
    path = _snapshot.get("path")
    if not path or not _uses_db(item):
        return

    from django.core.management import call_command
    from wagtail.models import Locale

    with _snapshot["blocker"].unblock():
        if not Locale.objects.exists():
            call_command("loaddata", path, verbosity=0)
