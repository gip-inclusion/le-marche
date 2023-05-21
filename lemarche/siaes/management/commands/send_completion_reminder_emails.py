from django.core.management.base import BaseCommand

from lemarche.siaes.models import Siae
from lemarche.siaes.tasks import send_completion_reminder_email_to_siae


class Command(BaseCommand):
    """
    (Monthly) script to contact Siaes which have not yet completed their content

    Usage:
    python manage.py send_completion_reminder_emails --dry-run
    python manage.py send_completion_reminder_emails
    """

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Dry run, no sends")

    def handle(self, dry_run=False, **options):
        self.stdout.write("-" * 80)
        self.stdout.write("Script to send Siae completion reminder emails...")

        self.stdout.write("-" * 80)
        self.stdout.write("Step 1: Find Siae")

        siae_reminder_list = Siae.objects.content_not_filled().filter(user_count__gte=1)
        self.stdout.write(f"Found {siae_reminder_list.count()} Siae to remind")

        if not dry_run:
            self.stdout.write("-" * 80)
            self.stdout.write("Step 2: Send emails to each Siae user(s)")
            for siae in siae_reminder_list:
                send_completion_reminder_email_to_siae(siae)

        self.stdout.write("-" * 80)
        self.stdout.write("Done!")
