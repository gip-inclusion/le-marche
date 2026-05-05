from itertools import batched

from sentry_sdk.crons import monitor

from lemarche.siaes import utils as siae_utils
from lemarche.siaes.models import Siae
from lemarche.utils.apis import api_slack
from lemarche.utils.commands import BaseCommand


class Command(BaseCommand):
    """
    Goal: update the '_count' fields of each Siae

    Note: some of these fields are updated on each Siae save()

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

    @monitor(monitor_slug="update_siae_count_fields")
    def handle(self, *args, **options):
        self.stdout_messages_info("Updating Siae count fields...")

        # Step 1a: build the queryset
        siae_queryset = (
            Siae.objects.prefetch_many_to_many()
            .prefetch_many_to_one()
            .prefetch_related("users", "groups", "labels")
            .with_tender_stats()
            .all()
        )
        if options["id"]:
            siae_queryset = siae_queryset.filter(id=options["id"])
        total = siae_queryset.count()
        self.stdout_messages_info(f"Found {total} siaes")

        # Step 1b: init fields to update
        update_fields = options["fields"] if options["fields"] else Siae.FIELDS_STATS_COUNT
        self.stdout_messages_info(f"Fields to update: {update_fields}")

        batch_count = 0
        BATCH_SIZE = 1_000
        for batch in batched(siae_queryset, BATCH_SIZE):
            siaes = list(batch)
            for siae in siaes:
                # M2M
                siae.user_count = siae.users.count()
                siae.sector_count = siae.activities.values_list("sector__group").distinct().count()
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
                siae.tender_detail_not_interested_count = siae.tender_detail_not_interested_count_annotated

            Siae.objects.bulk_update(siaes, update_fields)
            batch_count += 1
            self.stdout_info(f"{min(total, batch_count * BATCH_SIZE)} ...")

        msg_success = [
            "----- Siae count fields -----",
            f"Done! Processed {siae_queryset.count()} siaes",
            f"Fields updated: {update_fields}",
        ]
        self.stdout_messages_success(msg_success)
        api_slack.send_message_to_channel("\n".join(msg_success))
