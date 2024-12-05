import time
from datetime import timedelta

from django.utils import timezone

from lemarche.siaes.models import Siae
from lemarche.utils.apis import api_brevo
from lemarche.utils.commands import BaseCommand


two_weeks_ago = timezone.now() - timedelta(weeks=2)


class Command(BaseCommand):
    """
    Script to send Siae to Brevo CRM (companies)

    Usage:
    python manage.py crm_brevo_sync_companies --recently-updated
    python manage.py crm_brevo_sync_companies
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--recently-updated", dest="recently_updated", action="store_true", help="Only sync recently updated Siaes"
        )

    def handle(self, recently_updated: bool, **options):
        self.stdout.write("-" * 80)
        self.stdout.write("Script to sync Siaes with Brevo CRM (companies)...")

        # Step 1: build the queryset
        siaes_qs = Siae.objects.all()
        self.stdout.write(f"Sync Siae > Brevo: we have {Siae.objects.count()} siaes")
        # Update only the recently updated siaes
        if recently_updated:
            siaes_qs = siaes_qs.filter(updated_at__gte=two_weeks_ago)
            self.stdout.write(f"Sync Siae > Brevo: {siaes_qs.count()} recently updated")

        # Step 2: Add the 90-day limited annotations
        siaes_qs = siaes_qs.with_tender_stats(since_days=90)

        # Step 3: loop on the siaes
        for index, siae in enumerate(siaes_qs):
            new_extra_data = {
                "completion_rate": siae.completion_rate if siae.completion_rate is not None else 0,
                "tender_received": siae.tender_email_send_count_annotated,
                "tender_interest": siae.tender_detail_contact_click_count_annotated,
            }

            # extra_data update if needed
            if siae.extra_data != new_extra_data:
                siae.extra_data.update(
                    {
                        "brevo_company_data": new_extra_data,
                    }
                )
                siae.save(update_fields=["extra_data"])

            api_brevo.create_or_update_company(siae)
            if (index % 10) == 0:  # avoid API rate-limiting
                time.sleep(1)
            if (index % 500) == 0:
                print(f"{index}...")
