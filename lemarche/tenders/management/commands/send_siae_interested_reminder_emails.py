from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from lemarche.tenders.models import Tender, TenderSiae
from lemarche.www.tenders.tasks import send_tender_interested_reminder_email_to_siaes


class Command(BaseCommand):
    """
    Daily script to check recently contact click. send reminder
    When? J+2 (but doesn't run on weekends!)

    Usage:
    python manage.py send_siae_interested_reminder_emails --dry-run
    python manage.py send_siae_interested_reminder_emails --days-since-detail-contact-click-date 2
    python manage.py send_siae_interested_reminder_emails --tender-id 1
    python manage.py send_siae_interested_reminder_emails
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--days-since-detail-contact-click-date",
            dest="days_since_detail_contact_click_date",
            type=int,
            default=2,
            help="Laps de temps depuis 'detail_contact_click_date'",
        )
        parser.add_argument(
            "--tender-id", dest="tender_id", type=int, default=None, help="Restreindre sur un besoin donné"
        )
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Dry run, no sends")

    def handle(self, dry_run=False, **options):
        self.stdout.write("-" * 80)
        self.stdout.write("Script to send Siae interested reminder emails...")

        current_weekday = timezone.now().weekday()
        if current_weekday >= 5:
            self.stdout.write("Weekend... Stopping. Come back on Monday :)")
        else:
            self.stdout.write("-" * 80)
            self.stdout.write("Step 1: Find TenderSiae")
            self.stdout.write(f"- where detail_contact_click_date J+{options['days_since_detail_contact_click_date']}")

            lt_days_ago = timezone.now() - timedelta(days=options["days_since_detail_contact_click_date"])
            gte_days_ago = timezone.now() - timedelta(days=options["days_since_detail_contact_click_date"] + 1)
            # Monday: special case (the script doesn't run during on weekends)
            # gte_days_ago = gte_days_ago+2 to account for Saturday & Sunday
            if current_weekday == 0:
                gte_days_ago = timezone.now() - timedelta(days=options["days_since_detail_contact_click_date"] + 1 + 2)
            tendersiae_interested_reminder_list = TenderSiae.objects.detail_contact_click_post_reminder(
                gte_days_ago=gte_days_ago, lt_days_ago=lt_days_ago
            )

            if options["tender_id"]:
                tendersiae_interested_reminder_list = tendersiae_interested_reminder_list.filter(
                    tender_id=options["tender_id"]
                )
            self.stdout.write(f"Found {tendersiae_interested_reminder_list.count()} TenderSiaes to remind")

            if not dry_run:
                self.stdout.write("-" * 80)
                self.stdout.write("Step 2: Send emails for each tender")
                tender_id_list = (
                    tendersiae_interested_reminder_list.values_list("tender_id", flat=True).distinct().order_by()
                )
                self.stdout.write(f"{tender_id_list.count()} tenders concerned")
                for tender_id in tender_id_list:
                    tender = Tender.objects.get(id=tender_id)
                    tender_tendersiae_interested_reminder_list = tendersiae_interested_reminder_list.filter(
                        tender_id=tender_id
                    )
                    tender_tendersiae = TenderSiae.objects.filter(tender_id=tender_id).filter(
                        email_send_date__isnull=False
                    )
                    self.stdout.write(
                        f"Tender {tender_id}: {tender_tendersiae_interested_reminder_list.count()} TenderSiaes to remind (out of {tender_tendersiae.count()})"  # noqa
                    )
                    send_tender_interested_reminder_email_to_siaes(
                        tender, days_since_detail_contact_click_date=options["days_since_detail_contact_click_date"]
                    )
                    self.stdout.write("Emails sent")

            self.stdout.write("-" * 80)
            self.stdout.write("Done!")
