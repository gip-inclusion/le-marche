from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from lemarche.stats.models import Tracker
from lemarche.utils.db import secure_delete


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            dest="dry_run",
            action="store_true",
            help="La commande est exécutée sans que les modifications soient transmises à la base",
        )

    def handle(self, *args, **options):
        expiry_date = timezone.now() - relativedelta(months=settings.TRACKER_DELETION_TIMEOUT_IN_MONTHS)

        # retrieve old trackers to delete
        trackers_qs = Tracker.objects.filter(date_created__lte=expiry_date)

        if options["dry_run"]:
            self.stdout.write(
                f"Dry-run: suppression des anciens trackers: {trackers_qs.count()} auraient été supprimés"
            )
            return

        deleted = secure_delete(trackers_qs, ["stats.Tracker"])
        log = f"Suppression des anciens trackers: {deleted.get('stats.Tracker')} ont été supprimés"
        if deleted:
            log += f" ({deleted})"
        self.stdout.write(log)
