import argparse

from django.db.utils import IntegrityError

from lemarche.stats.models import StatsUser
from lemarche.users.models import User
from lemarche.utils.commands import BaseCommand


class Command(BaseCommand):
    """
    Import users from the app db to the stats db.
    Before the insert we clean the table of users in stats db

    Usage:
    poetry run python manage.py import_users_for_stats
    poetry run python manage.py import_users_for_stats --clean
    poetry run python manage.py import_users_for_stats --no-clean
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "-C",
            "--clean",
            action=argparse.BooleanOptionalAction,
            default=True,
            help="Effacer la table des utilisateurs la db de stat",
        )

    def handle(self, *args, **options):
        if options["clean"]:
            self.stdout_success("-" * 80)
            self.stdout_info("Step 0: clean user table in the stats db")
            count_delete = self.clean_stats_users()
            self.stdout_success(f"Deleted {count_delete} from the stats db")

        self.stdout_info("Step 1: fetching download list of users")
        users_list = self.fetch_users_list()
        self.stdout_success(f"Found {len(users_list)} items")

        self.stdout_info("Step 2: upload user list to stats db")
        stats_users = self.upload_users_to_db_stats(users_list)
        if stats_users:
            self.stdout_success(f"Insert {len(stats_users)} items")

        self.stdout_success("-" * 80)

    def fetch_users_list(self):
        users = User.objects.all()
        list_stats_attrs = [field.name for field in StatsUser._meta.fields]
        return users.values(*list_stats_attrs)

    def upload_users_to_db_stats(self, users_list):
        stats_users_list = [StatsUser(**params) for params in users_list]
        try:
            return StatsUser.objects.bulk_create(stats_users_list, batch_size=50)
        except IntegrityError as e:
            self.stdout_error(e)

    def clean_stats_users(self):
        count_delete, _ = StatsUser.objects.all().delete()
        return count_delete
