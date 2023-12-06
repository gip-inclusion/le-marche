from lemarche.siaes import utils as siae_utils
from lemarche.siaes.models import Siae
from lemarche.utils.apis import api_slack
from lemarche.utils.commands import BaseCommand


class Command(BaseCommand):
    """
    Goal: update the '_count' fields of each Siae

    Note: these fields should be updated automatically on each Siae save()

    Usage:
    python manage.py update_siae_count_fields
    python manage.py update_siae_count_fields --id 1
    python manage.py update_siae_count_fields --id 1 --fields user_count
    python manage.py update_siae_count_fields --id 1 --fields user_count --fields etablissement_count
    """

    def add_arguments(self, parser):
        parser.add_argument("--id", type=int, default=None, help="Indiquer l'ID d'une structure")
        parser.add_argument(
            "--fields", action="append", default=[], help="Filtrer sur les champs count à mettre à jour"
        )

    def handle(self, *args, **options):
        self.stdout_messages_info("Updating Siae count fields...")

        # Step 1a: build the queryset
        siae_queryset = (
            Siae.objects.prefetch_many_to_many()
            .prefetch_many_to_one()
            .prefetch("users", "groups", "labels")
            .with_tender_stats()
            .all()
        )
        if options["id"]:
            siae_queryset = siae_queryset.filter(id=options["id"])
        self.stdout_messages_info(f"Found {siae_queryset.count()} siaes")

        # Step 1b: init fields to update
        update_fields = options["fields"] if options["fields"] else Siae.FIELDS_STATS_COUNT
        self.stdout_messages_info(f"Fields to update: {update_fields}")

        # Step 2: loop on each Siae
        progress = 0
        for index, siae in enumerate(siae_queryset):
            # M2M
            siae.user_count = siae.users.count()
            siae.sector_count = siae.sectors.count()
            siae.network_count = siae.networks.count()
            siae.group_count = siae.groups.count()
            # FK
            siae.offer_count = siae.offers.count()
            siae.client_reference_count = siae.client_references.count()
            siae.label_count = siae.labels_old.count()
            siae.image_count = siae.images.count()
            # etablissement_count
            if siae.is_active and siae.siren:
                siae.etablissement_count = siae_utils.calculate_etablissement_count(siae)
            # completion_rate
            siae.completion_rate = siae.completion_rate_calculated
            # tenders
            siae.tender_count = siae.tender_count_annotated
            siae.tender_email_send_count = siae.tender_email_send_count_annotated
            siae.tender_email_link_click_count = siae.tender_email_link_click_count_annotated
            siae.tender_detail_display_count = siae.tender_detail_display_count_annotated
            siae.tender_detail_contact_click_count = siae.tender_detail_contact_click_count_annotated

            # Step 3: update count fields
            siae.save(update_fields=update_fields)

            progress += 1
            if (progress % 500) == 0:
                self.stdout_info(f"{progress}...")

        msg_success = [
            "----- Siae count fields -----",
            f"Done! Processed {siae_queryset.count()} siaes",
            f"Fields updated: {update_fields}",
        ]
        self.stdout_messages_success(msg_success)
        api_slack.send_message_to_channel("\n".join(msg_success))
