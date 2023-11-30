from django.core.management.base import BaseCommand

from lemarche.tenders.models import Tender
from lemarche.www.tenders.tasks import send_validated_tender


class Command(BaseCommand):
    """
    Command to send validated tenders

    Usage: python manage.py send_validated_tenders
    """

    def handle(self, *args, **options):
        validated_tenders_to_send = Tender.objects.validated_but_not_sent()
        if validated_tenders_to_send.count():
            self.stdout.write(f"Found {validated_tenders_to_send.count()} validated tender(s) to send")
            for tender in validated_tenders_to_send:
                send_validated_tender(tender)
