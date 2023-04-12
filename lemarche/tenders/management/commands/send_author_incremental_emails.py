from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from lemarche.tenders.models import Tender
from lemarche.www.tenders.tasks import send_author_incremental_2_days_email


class Command(BaseCommand):
    """
    Daily script to check recently validated Tenders. If incremental, then contact author
    When? J+2

    Usage:
    python manage.py send_author_incremental_emails --dry-run
    python manage.py send_author_incremental_emails
    """

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Dry run, no sends")

    def handle(self, dry_run=False, **options):
        self.stdout.write("-" * 80)
        self.stdout.write("Script to send Tender incremental emails...")

        self.stdout.write("-" * 80)
        self.stdout.write("Step 1: Find Tender validated J+2")
        two_days_ago = timezone.now() - timedelta(days=2)
        three_days_ago = timezone.now() - timedelta(days=3)
        tender_validated_incremental = Tender.objects.validated().is_incremental()
        tender_validated_incremental_2_days = tender_validated_incremental.filter(
            created_at__gte=three_days_ago
        ).filter(created_at__lt=two_days_ago)
        self.stdout.write(f"Found {tender_validated_incremental_2_days.count()} Tenders")

        if not dry_run:
            self.stdout.write("-" * 80)
            self.stdout.write("Step 2: Send emails")
            for tender in tender_validated_incremental_2_days:
                send_author_incremental_2_days_email(tender)
            self.stdout.write(f"Sent {tender_validated_incremental_2_days.count()} J+2 emails")

        self.stdout.write("-" * 80)
        self.stdout.write("Done!")
