from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from lemarche.siaes.models import SiaeUserRequest
from lemarche.www.dashboard.tasks import (
    send_siae_user_request_reminder_3_days_emails,
    send_siae_user_request_reminder_8_days_emails,
)


class Command(BaseCommand):
    """
    Daily script to check pending SiaeUserRequest, and send reminder emails
    When? J+3 & J+8

    Usage:
    python manage.py send_siae_user_request_reminder_emails --dry-run
    python manage.py send_siae_user_request_reminder_emails
    """

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Dry run, no sends")

    def handle(self, dry_run=False, **options):
        self.stdout.write("-" * 80)
        self.stdout.write("Script to send SiaeUserRequest reminder emails...")

        self.stdout.write("-" * 80)
        self.stdout.write("Step 1: SiaeUserRequest J+3 reminders")
        three_days_ago = timezone.now() - timedelta(days=3)
        four_days_ago = timezone.now() - timedelta(days=4)
        siae_user_request_pending = SiaeUserRequest.objects.pending()
        siae_user_request_reminder_3_days = siae_user_request_pending.filter(created_at__gte=four_days_ago).filter(
            created_at__lt=three_days_ago
        )
        self.stdout.write(f"Found {siae_user_request_reminder_3_days.count()} SiaeUserRequests")

        if not dry_run:
            for siae_user_request in siae_user_request_reminder_3_days:
                send_siae_user_request_reminder_3_days_emails(siae_user_request)
            self.stdout.write(f"Sent {siae_user_request_reminder_3_days.count()} J+3 reminders")

        self.stdout.write("-" * 80)
        self.stdout.write("Step 2: SiaeUserRequest J+8 reminders")
        eight_days_ago = timezone.now() - timedelta(days=8)
        nine_days_ago = timezone.now() - timedelta(days=9)
        siae_user_request_pending = SiaeUserRequest.objects.pending()
        siae_user_request_reminder_8_days = siae_user_request_pending.filter(created_at__gte=nine_days_ago).filter(
            created_at__lt=eight_days_ago
        )
        self.stdout.write(f"Found {siae_user_request_reminder_8_days.count()} SiaeUserRequests")

        if not dry_run:
            for siae_user_request in siae_user_request_reminder_8_days:
                send_siae_user_request_reminder_8_days_emails(siae_user_request)
            self.stdout.write(f"Sent {siae_user_request_reminder_8_days.count()} J+8 reminders")

        self.stdout.write("-" * 80)
        self.stdout.write("Done!")
