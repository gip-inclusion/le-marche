from lemarche.tenders.models import Tender
from lemarche.utils.commands import BaseCommand


TENDER_COUNT_FIELDS = [
    "siae_count",
    "siae_email_send_count",
    "siae_email_link_click_count",
    "siae_detail_display_count",
    "siae_email_link_click_or_detail_display_count",
    "siae_detail_contact_click_count",
]


class Command(BaseCommand):
    """
    Goal: update the '_count' fields of each Tender

    Usage:
    python manage.py update_tender_count_fields
    python manage.py update_tender_count_fields --id 1
    python manage.py update_tender_count_fields --id 1 --fields siae_count
    python manage.py update_tender_count_fields --id 1 --fields siae_count --fields siae_detail_contact_click_count
    """

    def add_arguments(self, parser):
        parser.add_argument("--id", type=int, default=None, help="Indiquer l'ID d'un besoin")
        parser.add_argument(
            "--fields", action="append", default=[], help="Filtrer sur les champs count à mettre à jour"
        )

    def handle(self, *args, **options):
        self.stdout_messages_info("Updating Tender count fields...")

        # Step 1a: build the queryset
        tender_queryset = Tender.objects.with_siae_stats().all()
        if options["id"]:
            tender_queryset = tender_queryset.filter(id=options["id"])
        self.stdout_messages_info(f"Found {tender_queryset.count()} tenders")

        # Step 1b: init fields to update
        update_fields = options["fields"] if options["fields"] else TENDER_COUNT_FIELDS
        self.stdout_messages_info(f"Fields to update: {update_fields}")

        # Step 2: loop on each Tender
        progress = 0
        for index, tender in enumerate(tender_queryset):
            # M2M
            tender.siae_count = tender.siae_count_annotated
            tender.siae_email_send_count = tender.siae_email_send_count_annotated
            tender.siae_email_link_click_count = tender.siae_email_link_click_count_annotated
            tender.siae_detail_display_count = tender.siae_detail_display_count_annotated
            tender.siae_email_link_click_or_detail_display_count = (
                tender.siae_email_link_click_or_detail_display_count_annotated
            )
            tender.siae_detail_contact_click_count = tender.siae_detail_contact_click_count_annotated

            # Step 3: update count fields
            tender.save(update_fields=update_fields)

            progress += 1
            if (progress % 500) == 0:
                self.stdout_info(f"{progress}...")

        msg_success = [
            "----- Tender count fields -----",
            f"Done! Processed {tender_queryset.count()} tenders",
            f"Fields updated: {update_fields}",
        ]
        self.stdout_messages_success(msg_success)