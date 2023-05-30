import calendar

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from lemarche.siaes.models import Siae
from lemarche.siaes.tasks import send_completion_reminder_email_to_siae
from lemarche.utils.apis import api_slack


class Command(BaseCommand):
    """
    (Monthly) script to contact Siaes which have not yet completed their content

    Usage:
    python manage.py send_completion_reminder_emails --day-of-week 1
    python manage.py send_completion_reminder_emails --day-of-week 1 --day-of-month last
    python manage.py send_completion_reminder_emails --dry-run
    python manage.py send_completion_reminder_emails
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--day-of-week",
            dest="day_of_week",
            type=int,
            help="Lundi = 0 ; Dimanche = 6",
        )
        parser.add_argument(
            "--day-of-month",
            dest="day_of_month",
            type=str,
            help="'first' for the first weekday of the month ; 'last' for the last weekday of the month",
        )
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Dry run, no sends")

    def handle(self, dry_run=False, **options):
        self.stdout.write("-" * 80)
        self.stdout.write("Script to send Siae completion reminder emails...")

        if options["day_of_week"] is not None:
            if options["day_of_week"] != timezone.now().weekday():
                raise CommandError("Day of week not compatible with day_of_week parameter. Stopping.")

        if options["day_of_month"] is not None:
            current_year = timezone.now().year
            current_month = timezone.now().month
            current_day = timezone.now().day
            current_month_day_count = calendar.monthrange(year=current_year, month=current_month)[1]
            if (options["day_of_month"] == "first") and (current_day > 7):
                raise CommandError("Not the first weekday of the month. Stopping.")
            elif (options["day_of_month"] == "last") and (current_month_day_count - current_day >= 7):
                raise CommandError("Not the last weekday of the month. Stopping.")

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
        msg_success = [
            "----- Complétion fiches structures (e-mails de rappel) -----",
            f"Siae contacted: {siae_reminder_list.count()}",
        ]
        self.stdout_messages_success(msg_success)
        api_slack.send_message_to_channel("\n".join(msg_success))
