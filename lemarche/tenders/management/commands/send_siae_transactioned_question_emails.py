from datetime import datetime, timedelta

from django.core.management.base import BaseCommand

from lemarche.tenders.models import TenderSiae
from lemarche.www.tenders.tasks import send_tenders_siae_survey


seven_days_ago = datetime.today().date() - timedelta(days=7)


class Command(BaseCommand):
    """
    Daily script to send an email to tender siaes
    Rules
    - Tender must be "sent"
    - Siae must be "interested"
    - Siae must not have received a survey yet
    When?
    - J+7 after tender start_working_date

    Usage:
    python manage.py send_siae_transactioned_question_emails --dry-run
    python manage.py send_siae_transactioned_question_emails
    """

    def add_arguments(self, parser):
        parser.add_argument("--kind", type=str, dest="kind")
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Dry run, no sends")

    def handle(self, kind=None, reminder=False, dry_run=False, **options):
        self.stdout.write("Script to send email tender transactioned_question to interested siaes...")

        # tender must be sent & start_working_date J+7
        tendersiae_qs = TenderSiae.objects.filter(
            tender__first_sent_at__isnull=False, tender__start_working_date=seven_days_ago
        )
        # siae must be interested
        tendersiae_qs = tendersiae_qs.filter(detail_contact_click_date__isnull=False)
        # siae must not have received the survey yet
        tendersiae_qs = tendersiae_qs.filter(survey_transactioned_answer=None, survey_transactioned_send_date=None)

        self.stdout.write(f"Found {tendersiae_qs.count()} tendersiaes")

        if not dry_run:
            email_kind = "transactioned_question_7d"
            for tendersiae in tendersiae_qs:
                send_tenders_siae_survey(tendersiae, kind=email_kind)
            self.stdout.write(f"Sent {tendersiae.count()} {email_kind}")
