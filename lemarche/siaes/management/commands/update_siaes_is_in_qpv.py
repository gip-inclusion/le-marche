import logging
import time
from datetime import datetime, timedelta

from django.db.models import Q
from django.core.management.base import BaseCommand
from django.utils import timezone

from lemarche.siaes.models import Siae
from lemarche.utils.apis.api_qpv import is_in_qpv, IS_QPV_KEY, QPV_CODE_KEY, QPV_NAME_KEY


class Command(BaseCommand):
    """
    Populates API Entreprise fields

    Note: Only on Siae who have api_entreprise_*_last_sync_date as None

    TODO: filter only on Siae not updated since a certain date?

    Usage: poetry run python manage.py update_siaes_is_in_qpv
    Usage: poetry run python manage.py update_siaes_is_in_qpv --limit 10
    """

    FIELDS_TO_BULK_UPDATE = ["is_qpv", "api_qpv_last_sync_date", "qpv_code", "qpv_name"]

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=None, help="Limiter le nombre de structures à processer")

    def handle(self, *args, **options):
        self.stdout.write("-" * 80)
        self.stdout.write("Populating API QPV...")
        two_months_ago = datetime.now() - timedelta(days=60)
        siae_list = Siae.objects.filter(
            (Q(api_qpv_last_sync_date__gte=two_months_ago) | Q(api_qpv_last_sync_date__isnull=True))
            & Q(coords__isnull=False)
        ).order_by("id")

        if options["limit"]:
            siae_list = siae_list[: options["limit"]]

        progress = 0
        success_count = {"etablissement": 0, "etablissement_qpv": 0}

        self.stdout.write(f"Found {len(siae_list)} Siae")

        for siae in siae_list:
            progress += 1
            if (progress % 50) == 0:
                self.stdout.write(f"{progress}...")

            result_is_in_qpv = is_in_qpv(siae.latitude, siae.longitude)
            success_count["etablissement"] += 1
            siae.is_qpv = result_is_in_qpv[IS_QPV_KEY]
            siae.api_qpv_last_sync_date = timezone.now()
            if siae.is_qpv:
                siae.qpv_code = result_is_in_qpv[QPV_CODE_KEY]
                siae.qpv_name = result_is_in_qpv[QPV_NAME_KEY]
                success_count["etablissement_qpv"] += 1
            else:
                siae.qpv_code = ""
                siae.qpv_name = ""
            # small delay to avoid going above the API limitation
            # "max. 250 requêtes/min/jeton cumulées sur tous les endpoints"
            time.sleep(0.5)

        Siae.objects.bulk_update(siae_list, self.FIELDS_TO_BULK_UPDATE)

        self.stdout.write("-" * 80)
        self.stdout.write(f"Done! Processed {len(siae_list)} siae")
        self.stdout.write(f"/etablissements success count: {success_count['etablissement']}/{len(siae_list)}")
        self.stdout.write(f"/exercices success count: {success_count['etablissement_qpv']}/{len(siae_list)}")

    # def siae_update_etablissement(siae):
    #     etablissement, error = Siae.objects.get()

    #     update_data = dict()

    #     if etablissement:
    #         # update_data"nature"] = Siae.NATURE_HEAD_OFFICE if etablissement["is_head_office"] else Siae.NATURE_ANTENNA  # noqa
    #         # update_data"is_active"] = False if not etablissement["is_closed"] else True
    #         if etablissement["employees"]:
    #             update_data["api_entreprise_employees"] = etablissement["employees"]
    #         if etablissement["employees_date_reference"]:
    #             update_data["api_entreprise_employees_year_reference"] = etablissement["employees_date_reference"]
    #         if etablissement["date_constitution"]:
    #             update_data["api_entreprise_date_constitution"] = etablissement["date_constitution"]
    #     # else:
    #     #     self.stdout.write(error)
    #     # TODO: if 404, siret_is_valid = False ?

    #     update_data["api_entreprise_etablissement_last_sync_date"] = timezone.now()
    #     Siae.objects.filter(id=siae.id).update(**update_data)

    #     return 1 if etablissement else 0
