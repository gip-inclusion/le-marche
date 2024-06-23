import datetime

from django.utils import timezone

from lemarche.analytics.utils import get_all_data_collectors
from lemarche.utils.commands import BaseCommand


class Command(BaseCommand):
    def add_arguments(self, parser):
        super().add_arguments(parser)

        parser.add_argument("--save", action="store_true", default=False, help="Save the data into the database")
        parser.add_argument("--offset", type=int, default=0, help="Offset the cutoff date by that number of days")

    def handle(self, *args, **options):
        before = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0) - datetime.timedelta(
            days=options["offset"]
        )
        self.stderr.write(f"Collecting analytics data before '{before!s}'.")

        data_collectors = get_all_data_collectors()
        save = options.get("save", False)
        for collector_class in data_collectors:
            collector_instance = collector_class()
            collector_instance.collect_and_save_data(before=before, save=save)
