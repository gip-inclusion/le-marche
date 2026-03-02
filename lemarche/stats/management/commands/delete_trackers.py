from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db.models.query_utils import Q
from lemarche.stats.models import Tracker
from lemarche.users.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--month_timeout",
            type=int,
            default=settings.TRACKER_DELETION_TIMEOUT_IN_MONTHS,
            help="Délai en mois à partir duquel les trackers doivent être supprimées",
        )

    def handle(self, *args, **options):
        expiry_date = timezone.now() - relativedelta(months=options["month_timeout"])
        qs = Tracker.objects.filter(date_created__lte=expiry_date)
        qs.delete()
