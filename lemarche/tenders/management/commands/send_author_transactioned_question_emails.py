from datetime import datetime, timedelta

from django.core.management.base import BaseCommand

from lemarche.tenders.models import Tender
from lemarche.www.tenders.tasks import send_tenders_author_feedback_or_survey


seven_days_ago = datetime.today().date() - timedelta(days=7)
one_day_ago = datetime.today().date() - timedelta(days=1)


class Command(BaseCommand):
    """
    Daily script to send an email to tender authors
    When? J+7 after tender deadline_date

    Usage:
    python manage.py send_author_transactioned_question_emails --dry-run
    python manage.py send_author_transactioned_question_emails --kind QUOTE
    python manage.py send_author_transactioned_question_emails --reminder
    python manage.py send_author_transactioned_question_emails
    """

    def add_arguments(self, parser):
        parser.add_argument("--kind", type=str, dest="kind")
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Dry run, no sends")
        parser.add_argument(
            "--reminder",
            dest="reminder",
            action="store_true",
            help="Send a second e-mail to authors who haven't responded to the first survey",
        )

    def handle(self, kind=None, reminder=False, dry_run=False, **options):
        self.stdout.write("-" * 80)
        self.stdout.write("Script to send email transactioned_question for tenders...")

        self.stdout.write("-" * 80)
        tender_qs = Tender.objects.sent()
        if kind:
            tender_qs = tender_qs.filter(kind=kind)
        if reminder:
            tender_qs = (
                tender_qs.exclude(survey_transactioned_send_date=None)
                .filter(survey_transactioned_answer=None)
                .filter(start_working_date=one_day_ago)
            )
        else:
            tender_qs = tender_qs.filter(survey_transactioned_send_date=None).filter(deadline_date=seven_days_ago)

        self.stdout.write(f"Found {tender_qs.count()} tenders")

        if not dry_run:
            email_kind = f"transactioned_question_7d{'_reminder' if reminder else ''}"
            for tender in tender_qs:
                send_tenders_author_feedback_or_survey(tender, kind=email_kind)
            self.stdout.write(f"Sent {tender_qs.count()} {email_kind}")

        self.stdout.write("-" * 80)
        self.stdout.write("Done!")
