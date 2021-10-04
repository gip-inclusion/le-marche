# https://github.com/betagouv/itou/blob/master/itou/users/migrations/0001bis_create_extensions.py

from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations


class Migration(migrations.Migration):
    """
    This migration has been added a posteriori to the list of existing
    migrations.

    It isn't possible to add this migration at the end of the list because its
    goal is to ensure the features provided by the extensions are already
    installed before there are used by the other migrations (gist index, etc).

    The 'users' app has been chosen as entry point because it's central
    dependency on the application and its migrations are processed early in the
    chain.

    On startup (excepted from the WSGI callable or if disabled), Django checks the
    consistency of the migrations in the database to ensure the graph of
    dependencies has been applied in the same order than indicated in
    django_migrations table. To make it happy, you can run this SQL query:

    insert into django_migrations (app, name, applied)
    select 'users', '0001bis_create_extensions', applied + interval '00:00:00.00001'
    from django_migrations
    where app = 'users' and name = '0001_initial';

    Note: this query wouldn't be necessary if this migration had been merged with
    users.0001_initial.
    """

    dependencies = [("users", "0001_initial")]

    operations = [
        TrigramExtension(),
    ]
