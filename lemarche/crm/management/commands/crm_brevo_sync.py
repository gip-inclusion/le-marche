import time
from datetime import timedelta

from django.utils import timezone

from lemarche.siaes.models import Siae
from lemarche.utils.apis import api_brevo
from lemarche.utils.commands import BaseCommand


ten_days_ago = timezone.now() - timedelta(days=4)


class Command(BaseCommand):
    """
    (Weekly) script to send Siae to Brevo CRM (companies)

    Usage:
    python manage.py crm_brevo_sync
    """

    def handle(self, **options):
        self.stdout.write("-" * 80)
        self.stdout.write("Script to sync with Brevo CRM...")

        # SIAE --> companies
        # Update only the recently updated
        siaes_qs = Siae.objects.filter(updated_at__lte=ten_days_ago)
        progress = 0

        self.stdout.write(
            f"Companies: updating our {Siae.objects.count()} siaes. {siaes_qs.count()} recently updated."
        )
        for siae in siaes_qs:
            api_brevo.create_or_update_company(siae)
            progress += 1
            if (progress % 10) == 0:  # avoid API rate-limiting
                time.sleep(1)
