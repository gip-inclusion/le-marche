from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from lemarche.tenders.models import TenderSiae
from lemarche.www.tenders.tasks import send_siae_reminder_email


class Command(BaseCommand):
    """
    Daily script to check recently sent emails to Siae. If no email_link_click_date, then send reminder
    When? J+2 (except weekends)

    Usage:
    python manage.py send_siae_reminder_emails --dry-run
    python manage.py send_siae_reminder_emails
    """

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Dry run, no sends")

    def handle(self, dry_run=False, **options):
        self.stdout.write("-" * 80)
        self.stdout.write("Script to send Siae reminder emails...")

        self.stdout.write("-" * 80)
        self.stdout.write("Step 1: Find TenderSiae email_send_date J+2 where email_link_click_date is None")
        two_days_ago = timezone.now() - timedelta(days=2)
        three_days_ago = timezone.now() - timedelta(days=3)
        tendersiae_2_days_reminder_list = (
            TenderSiae.objects.filter(email_send_date__gte=two_days_ago)
            .filter(email_send_date__lt=three_days_ago)
            .filter(email_link_click_date__isnull=True)
        )
        self.stdout.write(f"Found {tendersiae_2_days_reminder_list.count()} TenderSiaes to remind")

        if not dry_run:
            self.stdout.write("-" * 80)
            self.stdout.write("Step 2: Send emails")
            for tender in tendersiae_2_days_reminder_list:
                send_siae_reminder_email(tender)
            self.stdout.write(f"Sent {tendersiae_2_days_reminder_list.count()} J+2 emails")

        self.stdout.write("-" * 80)
        self.stdout.write("Done!")
