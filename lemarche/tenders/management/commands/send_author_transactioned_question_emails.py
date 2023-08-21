from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.db.models import Q

from lemarche.tenders.models import Tender
from lemarche.www.tenders.tasks import send_tenders_author_feedback_30_days


class Command(BaseCommand):
    """
    Daily script to send an email to tender authors
    When? J+30 after validation of tenders

    Usage:
    python manage.py send_author_transactioned_question_emails --dry-run
    python manage.py send_author_transactioned_question_emails
    """

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Dry run, no sends")
        parser.add_argument(
            "--all",
            dest="is_all_tenders",
            action="store_true",
            help="Send to all tenders validated 30 days ago or more",
        )

    def handle(self, dry_run=False, is_all_tenders=False, **options):
        self.stdout.write("-" * 80)
        self.stdout.write("Script to send email feedback for tenders...")

        self.stdout.write("-" * 80)
        thirty_days_ago = datetime.today().date() - timedelta(days=30)
        tenders_validated = Tender.objects.validated()
        if is_all_tenders:
            #  all tenders validated 30 days ago or more
            tenders_for_feedbacks = tenders_validated.filter(validated_at__date__lte=thirty_days_ago)
        else:
            # only tenders validated 30 days ago and up to 23/06/2022
            start_date_feature = datetime(2022, 6, 23).date()
            tenders_for_feedbacks = tenders_validated.filter(
                Q(validated_at__date=thirty_days_ago) & Q(validated_at__date__gte=start_date_feature)
            )

        self.stdout.write(f"Found {tenders_for_feedbacks.count()} tenders")

        if not dry_run:
            for tender in tenders_for_feedbacks:
                send_tenders_author_feedback_30_days(tender)
            self.stdout.write(f"Sent {tenders_for_feedbacks.count()} J+30 feedbacks")

        self.stdout.write("-" * 80)
        self.stdout.write("Done!")
