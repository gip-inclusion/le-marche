import pytest


def pytest_collection_modifyitems(items):
    """Auto-mark all tests with django_db so developers don't need to add the decorator manually."""
    for item in items:
        if not any(item.iter_markers("django_db")):
            item.add_marker(pytest.mark.django_db)
