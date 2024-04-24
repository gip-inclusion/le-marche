from datetime import timedelta

from django.utils import timezone

from lemarche.tenders.models import Tender
from lemarche.utils.commands import BaseCommand
from lemarche.www.tenders.tasks import send_super_siaes_email_to_author


class Command(BaseCommand):
    """
    Daily script to check tender without insterested siae,
    if it was sent first time more than two days ago, send email to author with list of five siaes with super badge
    When? J+2 (but doesn't run on weekends!)

    Usage:
    python manage.py send_author_list_of_super_siaes_emails --dry-run
    python manage.py send_author_list_of_super_siaes_emails --days-since-tender-sent-date 2
    python manage.py send_author_list_of_super_siaes_emails --tender-id 1
    python manage.py send_author_list_of_super_siaes_emails
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--days-since-tender-sent-date",
            dest="days_since_tender_sent_date",
            type=int,
            default=1,
            help="Laps de temps depuis la date du premier envoi (first_sent_at)",
        )
        parser.add_argument(
            "--tender-id", dest="tender_id", type=int, default=None, help="Restreindre sur un besoin donné"
        )
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Dry run, no sends")

    def handle(self, dry_run=False, **options):
        self.stdout_info("Script to send Super Siae to tender author...")

        current_weekday = timezone.now().weekday()
        if current_weekday > 4:
            self.stdout_error("Weekend... Stopping. Come back on Monday :)")
        else:
            self.stdout_messages_info("Step 1: Find Tender")
            self.stdout_messages_info(
                f"- where sent J-{options['days_since_tender_sent_date']} and no siae interested"
            )

            lt_days_ago = timezone.now() - timedelta(days=options["days_since_tender_sent_date"])
            gte_days_ago = timezone.now() - timedelta(days=options["days_since_tender_sent_date"] + 1)
            # The script doesn't run on weekends
            if current_weekday == 0:
                gte_days_ago = gte_days_ago - timedelta(days=2)

            tender_list = Tender.objects.with_siae_stats().filter(
                first_sent_at__gte=gte_days_ago,
                first_sent_at__lt=lt_days_ago,
                siae_detail_contact_click_count_annotated=0,
            )
            if options["tender_id"]:
                tender_list = tender_list.filter(id=options["tender_id"])
            self.stdout_info(
                f"Found {tender_list.count()} Tender without siaes interested between {gte_days_ago} and {lt_days_ago}"
            )

            self.stdout_messages_info(f"Step 2: {'display top siaes' if dry_run else 'send emails'} for each tender")
            for tender in tender_list:
                top_siaes = tender.siaes.all().order_by_super_siaes()[:5]
                self.stdout_info(f"{top_siaes.count()} top siaes finded for #{tender.id} {tender}")
                if len(top_siaes) > 1:
                    if not dry_run:
                        send_super_siaes_email_to_author(tender, top_siaes)
                        self.stdout_success(f"Email sent to tender author {tender.author}")
                    else:
                        for siae in top_siaes:
                            self.stdout_messages_info(
                                [
                                    siae.name_display,
                                    siae.get_kind_display(),
                                    siae.contact_full_name,
                                    siae.contact_phone,
                                    siae.contact_email,
                                ]
                            )
                else:
                    self.stdout_error(f"Not enough siaes to send an email for #{tender.id}")

            self.stdout_messages_success("Done!")
