from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.db.models import Q

from lemarche.tenders.models import Tender
from lemarche.www.tenders.tasks import send_tenders_author_feedback_or_survey


class Command(BaseCommand):
    """
    Daily script to send an email to tender authors
    When? J+30 after validation of tenders

    Usage:
    python manage.py send_author_transactioned_question_emails --dry-run
    python manage.py send_author_transactioned_question_emails --all
    python manage.py send_author_transactioned_question_emails --kind QUOTE
    python manage.py send_author_transactioned_question_emails
    """

    def add_arguments(self, parser):
        parser.add_argument("--kind", type=str, dest="kind")
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Dry run, no sends")
        parser.add_argument(
            "--all",
            dest="is_all_tenders",
            action="store_true",
            help="Send to all tenders with deadline_date 7 days ago",
        )

    def handle(self, kind=None, dry_run=False, is_all_tenders=False, **options):
        self.stdout.write("-" * 80)
        self.stdout.write("Script to send email transactioned_question for tenders...")

        self.stdout.write("-" * 80)
        seven_days_ago = datetime.today().date() - timedelta(days=7)
        # we first filter on validated tenders
        tender_qs = Tender.objects.validated()
        # we also filter on tenders who haven't answered to the email yet
        tender_qs = tender_qs.filter(survey_transactioned_answer=None)
        # optional filter on kind
        if kind:
            tender_qs = tender_qs.filter(kind=kind)
        # date filter
        if is_all_tenders:
            # all tenders with deadline_date 7 days or more
            tender_qs = tender_qs.filter(deadline_date__lte=seven_days_ago)
        else:
            # only tenders with deadline_date 7 days ago and up to 23/06/2022
            start_date_feature = datetime(2022, 6, 23).date()
            tender_qs = tender_qs.filter(Q(deadline_date=seven_days_ago) & Q(deadline_date__gte=start_date_feature))

        self.stdout.write(f"Found {tender_qs.count()} tenders")

        if not dry_run:
            for tender in tender_qs:
                send_tenders_author_feedback_or_survey(tender, kind="transactioned_question")
            self.stdout.write(f"Sent {tender_qs.count()} J+30 feedbacks")

        self.stdout.write("-" * 80)
        self.stdout.write("Done!")
