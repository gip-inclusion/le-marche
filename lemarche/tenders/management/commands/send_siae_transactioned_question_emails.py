from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from sentry_sdk.crons import monitor

from lemarche.tenders.models import Tender
from lemarche.www.tenders.tasks import send_tenders_siaes_survey


seven_days_ago = datetime.today().date() - timedelta(days=7)


class Command(BaseCommand):
    """
    Daily script to send an email to tender siaes
    Rules
    - Tender must be "sent" + no info on "transactioned"
    When?
    - J+7 after tender start_working_date

    Usage:
    python manage.py send_siae_transactioned_question_emails --dry-run
    python manage.py send_siae_transactioned_question_emails
    """

    def add_arguments(self, parser):
        parser.add_argument("--kind", type=str, dest="kind")
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Dry run, no sends")

    @monitor(monitor_slug="send_siae_transactioned_question_emails")
    def handle(self, kind=None, reminder=False, dry_run=False, **options):
        self.stdout.write("Script to send email tender transactioned_question to interested siaes...")

        # tender must be sent & no info on transaction & start_working_date J+7
        tender_qs = Tender.objects.sent().filter(siae_transactioned=None)
        tender_qs = tender_qs.filter(start_working_date=seven_days_ago)

        self.stdout.write(f"Found {tender_qs.count()} tenders")

        if not dry_run:
            email_kind = "transactioned_question_7d"
            for tender in tender_qs:
                send_tenders_siaes_survey(tender, kind=email_kind)
