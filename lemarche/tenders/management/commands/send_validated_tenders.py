from django.core.management.base import BaseCommand
from sentry_sdk.crons import monitor

from lemarche.tenders.models import Tender
from lemarche.www.tenders.tasks import send_validated_sent_batch_tender, send_validated_tender


class Command(BaseCommand):
    """
    Command to send validated tenders

    Note: run via a CRON
    "*/5 8-15 * * 1-5" = Every 5 minutes from 8am through 3pm, Monday through Friday
    https://cron.help/#*/5_8-15_*_*_1-5
    - why 8am and not 9am? because the server has UTC time
    - why 3pm and not 5pm? because UTC + will run until 15h55 included

    Usage: python manage.py send_validated_tenders
    """

    @monitor(monitor_slug="send_validated_tenders")
    def handle(self, *args, **options):
        # First send newly validated tenders
        validated_tenders_to_send = Tender.objects.validated_but_not_sent().is_not_outdated()
        if validated_tenders_to_send.count():
            self.stdout.write(f"Found {validated_tenders_to_send.count()} validated tender(s) to send")
            for tender in validated_tenders_to_send:
                send_validated_tender(tender)

        # Then look at already sent tenders (batch mode)
        validated_sent_tenders_batch_to_send = Tender.objects.validated_sent_batch().is_not_outdated()
        if validated_sent_tenders_batch_to_send.count():
            self.stdout.write(
                f"Found {validated_sent_tenders_batch_to_send.count()} validated sent tender(s) to batch"
            )
            for tender in validated_sent_tenders_batch_to_send:
                send_validated_sent_batch_tender(tender)
