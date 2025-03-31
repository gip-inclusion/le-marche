import csv
import os
import time

from django.db.models import Q
from django.utils import timezone
from sentry_sdk.crons import monitor

from lemarche.siaes.constants import SIAE_LEGAL_FORM_CHOICE_LIST
from lemarche.siaes.models import Siae
from lemarche.utils.apis import api_slack
from lemarche.utils.apis.api_recherche_entreprises import (
    RechercheEntreprisesAPIException,
    recherche_entreprises_get_or_error,
)
from lemarche.utils.commands import BaseCommand


SIAE_LEGAL_FORM_MAPPING_FILE_NAME = "data/mapping_api_entreprise_forme_juridique.csv"
SIAE_LEGAL_FORM_MAPPING_FILE_PATH = (
    os.path.dirname(os.path.realpath(__file__)) + "/" + SIAE_LEGAL_FORM_MAPPING_FILE_NAME
)


def read_csv(file_path):
    with open(file_path) as csv_file:
        row_list = list(csv.DictReader(csv_file, delimiter=","))

    return row_list


class Command(BaseCommand):
    """
    Populates API Entreprise fields with API Recherche Entreprises

    Note: Only on Siae who have api_entreprise_*_last_sync_date as None

    Usage:
    - poetry run python manage.py update_api_entreprise_fields
    - poetry run python manage.py update_api_entreprise_fields --siret 01234567891011
    - poetry run python manage.py update_api_entreprise_fields --limit 100
    """

    def add_arguments(self, parser):
        parser.add_argument("--siret", type=str, default=None, help="Lancer sur un Siret spécifique")
        parser.add_argument("--limit", type=int, default=None, help="Limiter le nombre de structures à processer")
        parser.add_argument("--wet-run", action="store_true", help="Exécuter les requêtes")

    @monitor(monitor_slug="update-api-entreprise-fields")
    def handle(self, *args, **options):
        self.stdout_info("-" * 80)
        self.stdout_info("Populating API Entreprise fields...")

        if options["siret"]:
            siae_queryset = Siae.objects.filter(siret=options["siret"])
        else:
            siae_queryset = Siae.objects.filter(
                Q(api_entreprise_entreprise_last_sync_date=None)
                | Q(api_entreprise_etablissement_last_sync_date=None)
                | Q(api_entreprise_exercice_last_sync_date=None)
            ).order_by("id")

        if options["limit"]:
            siae_queryset = siae_queryset[: options["limit"]]

        self._update_siae_api_entreprise_fields(siae_queryset, wet_run=options["wet_run"])

    def _update_siae_api_entreprise_fields(self, siae_queryset, wet_run=False):
        results = {"success": 0, "error": 0}
        mapping_file_row_list = read_csv(SIAE_LEGAL_FORM_MAPPING_FILE_PATH)

        progress = 0
        for siae in siae_queryset:
            progress += 1
            if (progress % 50) == 0:
                self.stdout_info(f"{progress}...")

            success = self._process_single_siae(siae, mapping_file_row_list, wet_run)
            if success:
                results["success"] += 1
            else:
                results["error"] += 1

            # small delay to avoid going above the API limitation
            time.sleep(0.2)

        total_count = siae_queryset.count()
        msg_success = [
            "----- Synchronisation API Entreprise -----",
            f"Done! Processed {total_count} siae",
            f"success count: {results['success']}/{total_count}",
            f"error count: {results['error']}/{total_count} (voir les logs)",
        ]
        self.stdout_messages_success(msg_success)
        api_slack.send_message_to_channel("\n".join(msg_success))

    def _process_single_siae(self, siae, mapping_file_row_list, wet_run):
        try:
            entreprise = recherche_entreprises_get_or_error(siae.siret)
            update_data = self._prepare_update_data(entreprise, mapping_file_row_list)

            if wet_run:
                Siae.objects.filter(id=siae.id).update(**update_data)
            else:
                self.stdout_info(f"Would update SIAE {siae.id} with {update_data=}")
            return True
        except RechercheEntreprisesAPIException as e:
            self.stdout_error(str(e))
            return False

    def _prepare_update_data(self, entreprise, mapping_file_row_list):
        update_data = {}

        # Forme juridique
        if entreprise.forme_juridique_code:
            self._update_forme_juridique(update_data, entreprise, mapping_file_row_list)

        # Etablissement
        update_data["api_entreprise_employees"] = (
            entreprise.employees if (entreprise.employees != "Unités non employeuses") else "Non renseigné"
        )
        update_data["api_entreprise_employees_year_reference"] = entreprise.employees_date_reference
        update_data["api_entreprise_date_constitution"] = entreprise.date_creation
        update_data["api_entreprise_etablissement_last_sync_date"] = timezone.now()

        # Exercice
        if entreprise.ca:
            update_data["api_entreprise_ca"] = entreprise.ca
            update_data["api_entreprise_exercice_last_sync_date"] = timezone.now()

        return update_data

    def _update_forme_juridique(self, update_data, entreprise, mapping_file_row_list):
        siae_mapping_row = next(
            (
                mapping_row
                for mapping_row in mapping_file_row_list
                if mapping_row["input_code"] == entreprise.forme_juridique_code
            ),
            None,
        )
        if siae_mapping_row and siae_mapping_row["output_name"] in SIAE_LEGAL_FORM_CHOICE_LIST:
            update_data["api_entreprise_forme_juridique"] = siae_mapping_row["output_name"]
            update_data["api_entreprise_forme_juridique_code"] = entreprise.forme_juridique_code
            update_data["api_entreprise_entreprise_last_sync_date"] = timezone.now()
        elif siae_mapping_row:
            raise ValueError(f"unknown output_name {siae_mapping_row['output_name']}")
        else:
            raise ValueError(f"unknown input_name {entreprise.forme_juridique_code}")
