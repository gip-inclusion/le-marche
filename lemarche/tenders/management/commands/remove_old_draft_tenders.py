from django.db.models.query_utils import Q
from dateutil.relativedelta import relativedelta
from lemarche.tenders.models import Tender
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    def handle(self, *args, **options):
        expiry_date = timezone.now() - relativedelta(months=12)

        qs = Tender.objects.filter(status=Tender.StatusChoices.STATUS_DRAFT, updated_at__lte=expiry_date)
        tenders_to_delete_count = qs.count()
        qs.delete()
        self.stdout.write(f"Besoins d'achat non-finalisés supprimés avec succès ({tenders_to_delete_count} traités)")
