import argparse
from datetime import timedelta

import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from lemarche.siaes.models import Siae
from lemarche.utils.apis.api_zrr import IS_ZRR_KEY, ZRR_CODE_KEY, ZRR_NAME_KEY, get_default_client, is_in_zrr


class Command(BaseCommand):
    """
    Populates API ZRR

    Note: Only on Siae who have coords, filter only on Siae not updated by the API since a two months

    Usage: poetry run python manage.py update_api_zrr_fields
    Usage: poetry run python manage.py update_api_zrr_fields --limit 10
    Usage: poetry run python manage.py update_api_zrr_fields --force
    Usage: poetry run python manage.py update_api_zrr_fields --limit 100 --no-force
    """

    def __init__(self, stdout=None, stderr=None, no_color=False):
        super().__init__(stdout, stderr, no_color)
        self.success_count = {"etablissement": 0, "etablissement_zrr": 0}

    FIELDS_TO_BULK_UPDATE = ["is_zrr", "api_zrr_last_sync_date", "zrr_code", "zrr_name"]

    def add_arguments(self, parser):
        parser.add_argument(
            "-L", "--limit", type=int, default=None, help="Limiter le nombre de structures à processer"
        )
        parser.add_argument(
            "-F",
            "--force",
            action=argparse.BooleanOptionalAction,
            default=None,
            help="Forcer l'update sans la vérification de la dernière mise à jour",
        )

    def get_query_set(self, **options):
        siaes_queryset = Siae.objects.filter(Q(coords__isnull=False)).order_by("id")

        if not options["force"]:
            since_last_date_limit = timezone.now() - timedelta(days=settings.API_QPV_RELATIVE_DAYS_TO_UPDATE)
            siaes_queryset = siaes_queryset.filter(
                (Q(api_zrr_last_sync_date__lte=since_last_date_limit) | Q(api_zrr_last_sync_date__isnull=True))
            )

        if options["limit"]:
            siaes_queryset = siaes_queryset[: options["limit"]]
        return siaes_queryset

    def handle(self, *args, **options):
        siae_list = self.get_query_set(**options)
        self.stdout_messages_info(["Populating API ZRR...", f"Found {len(siae_list)} Siae"])

        count_siae_to_update = 0
        client = get_default_client()
        try:
            siaes_to_update = []
            for siae in siae_list:
                # update siae from API
                siae = self.update_siae(client, siae)
                siaes_to_update.append(siae)
                # log progress
                count_siae_to_update = len(siaes_to_update)
                if (count_siae_to_update % 50) == 0:
                    self.stdout_info(f"{count_siae_to_update}...")

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            if status_code == 429:
                # the real exceed request error have code=10005, with the api
                # but requests send error code 429 "Unknown Status Code"
                self.stdout_error("exceeded the requests limit for today (5000/per day)")
        finally:
            client.close()
            # we still save siaes zrr status
            Siae.objects.bulk_update(
                siaes_to_update, self.FIELDS_TO_BULK_UPDATE, batch_size=settings.BATCH_SIZE_BULK_UPDATE
            )

        self.stdout_messages_sucess(
            [
                f"Done! Processed {len(siaes_to_update)}/{len(siae_list)} siaes",
                f"/Etablissements success count: {self.success_count['etablissement']}/{len(siaes_to_update)}",
                f"/Etablissements QPV success count: {self.success_count['etablissement_zrr']}/{len(siae_list)}",
            ]
        )

    def update_siae(self, client, siae):
        # call api is in zrr
        result_is_in_zrr = is_in_zrr(siae.latitude, siae.longitude, client=client)
        self.success_count["etablissement"] += 1
        siae.is_zrr = result_is_in_zrr[IS_ZRR_KEY]
        siae.api_zrr_last_sync_date = timezone.now()
        if siae.is_zrr:
            siae.zrr_code = result_is_in_zrr[ZRR_CODE_KEY]
            siae.zrr_name = result_is_in_zrr[ZRR_NAME_KEY]
            self.success_count["etablissement_zrr"] += 1
        else:
            siae.zrr_code = ""
            siae.zrr_name = ""
        return siae

    def stdout_success(self, message):
        return self.stdout.write(self.style.SUCCESS(message))

    def stdout_error(self, message):
        return self.stdout.write(self.style.ERROR(message))

    def stdout_info(self, message):
        return self.stdout.write(self.style.HTTP_INFO(message))

    def stdout_messages_info(self, messages):
        self.stdout_info("-" * 80)
        for message in messages:
            self.stdout_info(message)
        self.stdout_info("-" * 80)

    def stdout_messages_sucess(self, messages):
        self.stdout_success("-" * 80)
        for message in messages:
            self.stdout_success(message)
        self.stdout_success("-" * 80)
