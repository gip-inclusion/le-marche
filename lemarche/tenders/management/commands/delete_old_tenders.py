from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models.expressions import Q
from django.utils import timezone

from lemarche.tenders.models import Tender
from lemarche.utils.db import secure_delete


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            dest="dry_run",
            action="store_true",
            help="La commande est exécutée sans que les modifications soient transmises à la base",
        )

    def handle(self, *args, **options):
        expiry_date = timezone.now() - relativedelta(months=settings.TENDER_DELETION_TIMEOUT_IN_MONTHS)

        qs = Tender.objects.exclude(status=Tender.StatusChoices.STATUS_DRAFT).filter(
            Q(author__last_login__lte=expiry_date) | Q(author__last_login=None, author__date_joined__lte=expiry_date),
            published_at__lte=expiry_date,
            updated_at__lte=expiry_date,
        )

        if options["dry_run"]:
            self.stdout.write(
                f"Dry-run: suppression des besoins d'achat inactifs: {qs.count()} auraient été supprimés"
            )
            return

        deleted = secure_delete(
            qs,
            [
                "tenders.Tender",
                "tenders.Tender_admins",  # ManyToManyField on Tender
                "tenders.Tender_sectors",  # ManyToManyField on Tender
                "tenders.Tender_perimeters",  # ManyToManyField on Tender
                "conversations.TemplateTransactionalSendLog",  # Reverse Generic relation on Tender
                "tenders.TenderSiae",  # ManyToManyField on Tender
                "tenders.TenderQuestion",  # ForeignKey to Tender with on_delete=CASCADE
                "notes.Note",  # GenericForeignKey to Tender with on_delete=CASCADE
            ],
        )
        log = f"Suppression des besoins d'achat inactifs: {deleted.get('tenders.Tender')} ont été supprimés"
        if deleted:
            log += f" ({deleted})"
        self.stdout.write(log)
