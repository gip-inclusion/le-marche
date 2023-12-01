from django.core.management.base import BaseCommand

from lemarche.tenders.models import Tender
from lemarche.www.tenders.tasks import send_validated_tender


class Command(BaseCommand):
    """
    Command to send validated tenders

    Note: run via a CRON
    "*/5 9-17 * * 1-5" = Every 5 minutes from 9am through 5pm on Monday through Friday
    https://cron.help/#*/5_9-17_*_*_1-5

    Usage: python manage.py send_validated_tenders
    """

    def handle(self, *args, **options):
        validated_tenders_to_send = Tender.objects.validated_but_not_sent()
        if validated_tenders_to_send.count():
            self.stdout.write(f"Found {validated_tenders_to_send.count()} validated tender(s) to send")
            for tender in validated_tenders_to_send:
                send_validated_tender(tender)
