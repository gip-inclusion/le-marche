import argparse
from datetime import timedelta

import requests
from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from lemarche.siaes.models import Siae
from lemarche.utils.apis import api_slack
from lemarche.utils.commands import BaseCommand


class UpdateAPICommand(BaseCommand):
    """
    Base class for QPV and ZRR API fetch commands
    """

    API_NAME: str = None
    FIELDS_TO_BULK_UPDATE = []
    CLIENT = None

    def __init__(self, stdout=None, stderr=None, no_color=False):
        super().__init__(stdout, stderr, no_color)
        self.success_count = {"etablissement": 0, "etablissement_target": 0}

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

    @staticmethod
    def get_filter_query(date_limit) -> Q:
        """Qobjects to filter siaes_queryset"""
        raise NotImplementedError

    @staticmethod
    def is_in_target(latitude, longitude, client):
        raise NotImplementedError

    def get_query_set(self, **options):
        siaes_queryset = Siae.objects.filter(Q(coords__isnull=False)).order_by("id")

        if not options["force"]:
            since_last_date_limit = timezone.now() - timedelta(days=settings.API_QPV_RELATIVE_DAYS_TO_UPDATE)
            siaes_queryset = siaes_queryset.filter(self.get_filter_query(since_last_date_limit))

        if options["limit"]:
            siaes_queryset = siaes_queryset[: options["limit"]]
        return siaes_queryset

    def handle(self, *args, **options):
        siae_list = self.get_query_set(**options)
        self.stdout_messages_info([f"Populating API {self.API_NAME}...", f"Found {len(siae_list)} Siae"])

        siaes_to_update = []
        try:
            for siae in siae_list:
                # update siae from API
                siae = self.update_siae(siae)
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
            self.CLIENT.close()
            # we still save siaes target status
            Siae.objects.bulk_update(
                siaes_to_update, self.FIELDS_TO_BULK_UPDATE, batch_size=settings.BATCH_SIZE_BULK_UPDATE
            )

            msg_success = [
                f"----- Synchronisation API {self.API_NAME} -----",
                f"Done! Processed {len(siaes_to_update)}/{len(siae_list)} siaes",
                f"success count: {self.success_count['etablissement']}/{len(siaes_to_update)}",
                f"True count: {self.success_count['etablissement_target']}/{len(siaes_to_update)}",
            ]
            self.stdout_messages_success(msg_success)
            api_slack.send_message_to_channel("\n".join(msg_success))
