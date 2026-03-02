from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db.models.query_utils import Q
from lemarche.stats.models import StatsUser
from lemarche.users.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--month_timeout",
            type=int,
            default=settings.STATS_DELETION_TIMEOUT_IN_MONTHS,
            help="Délai en mois à partir duquel les stats anonymisées doivent être supprimées",
        )

    def handle(self, *args, **options):
        expiry_date = timezone.now() - relativedelta(months=options["month_timeout"])
        qs = StatsUser.objects.filter(is_anonymized=True, anonymized_at__lte=expiry_date)
        qs.delete()
