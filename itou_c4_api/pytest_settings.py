from itou_c4_api.settings import *
from django.test.runner import DiscoverRunner

UNDER_TEST = True


class DisableMigrations(object):
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


class UnManagedModelTestRunner(DiscoverRunner):
    """
    Test runner that automatically makes all unmanaged models in your Django
    project managed for the duration of the test run.
    """

    def setup_test_environment(self, *args, **kwargs):
        from django.apps import apps

        self.unmanaged_models = [
            m for m in apps.get_models() if not m._meta.managed
        ]
        for m in self.unmanaged_models:
            m._meta.managed = True
        super(UnManagedModelTestRunner, self).setup_test_environment(
            *args, **kwargs
        )

    def teardown_test_environment(self, *args, **kwargs):
        super(UnManagedModelTestRunner, self).teardown_test_environment(
            *args, **kwargs
        )
        # reset unmanaged models
        for m in self.unmanaged_models:
            m._meta.managed = False


# Since we can't create a test db on the read-only host, and we
# want our test dbs created with sqlite rather than the default
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "itou_c4_api.sqlite3"),
        "TEST": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.path.join(BASE_DIR, "itou_c4_api.sqlite3"),
        },
    },
    "structures": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "itou_c4_api.sqlite3"),
        "TEST": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.path.join(BASE_DIR, "itou_c4_api.sqlite3"),
        },
    }
}
AUTHENTICATION_BACKENDS = ("django.contrib.auth.backends.ModelBackend",)

# Custom routers we're using to route certain ORM queries
# to the remote host conflict with our overridden db settings.
# Set DATABASE_ROUTERS to an empty list to return to the defaults
# during the test run.
DATABASE_ROUTERS = ["itou_c4_api.routers.CocoRouter"]

# Skip the migrations by setting "MIGRATION_MODULES"
# to the DisableMigrations class defined above
MIGRATION_MODULES = DisableMigrations()

# Set Django's test runner to the custom class defined above
TEST_RUNNER = "itou_c4_api.pytest_settings.UnManagedModelTestRunner"
