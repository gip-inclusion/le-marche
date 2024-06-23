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

        self._get_data(before)
        self.stderr.write("Analytics data computed.")

        # self.show_data(data)
        # if options["save"]:
        #     self.save_data(data, before)

    @staticmethod
    def _get_data(before):
        data_collectors = get_all_data_collectors()
        for collector_class in data_collectors:
            collector_instance = collector_class()
            collector_instance.collect_data()

    def show_data(self, data):
        for code, value in data.items():
            self.stdout.write(f"{code}: {value}")
