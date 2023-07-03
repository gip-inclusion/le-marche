import csv
import os

from lemarche.siaes import constants as siae_constants
from lemarche.siaes.models import Siae
from lemarche.utils.commands import BaseCommand


SIAE_LEGAL_FORM_MAPPING_FILE_NAME = "data/mapping_api_entreprise_forme_juridique.csv"
SIAE_LEGAL_FORM_MAPPING_FILE_PATH = (
    os.path.dirname(os.path.realpath(__file__)) + "/" + SIAE_LEGAL_FORM_MAPPING_FILE_NAME
)


def read_csv(file_path):
    row_list = list()

    with open(file_path) as csv_file:
        csvreader = csv.DictReader(csv_file, delimiter=",")
        for index, row in enumerate(csvreader):
            row_list.append(row)

    return row_list


class Command(BaseCommand):
    """
    Usage:
    - poetry run python manage.py set_legal_form_field --dry-run
    - poetry run python manage.py set_legal_form_field
    """

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Dry run (no changes to the DB)")

    def handle(self, *args, **options):
        self.stdout_info("-" * 80)
        self.stdout_info("Populating legal_form field...")

        siaes = Siae.objects.all()
        siaes_with_legal_form = siaes.exclude(legal_form="").exclude(legal_form__isnull=True)
        self.stdout_info("-" * 80)
        self.stdout_info(f"SIAE count: {siaes.count()}")
        self.stdout_info(f"SIAE with legal_form count: {siaes_with_legal_form.count()}")
        if not options["dry_run"]:
            siaes_with_legal_form.update(legal_form="")
            self.stdout_info("Emptied legal_form field!")

        mapping_file_row_list = read_csv(SIAE_LEGAL_FORM_MAPPING_FILE_PATH)

        self.stdout_info("-" * 80)
        self.stdout_info("Mapping...")
        progress = 0
        results = {"success": 0, "error": 0}

        for siae in siaes:
            if siae.api_entreprise_forme_juridique:
                siae_mapping_row = next(
                    (
                        mapping_row
                        for mapping_row in mapping_file_row_list
                        if mapping_row["input_name"] == siae.api_entreprise_forme_juridique
                    ),
                    None,
                )
                if siae_mapping_row:
                    if siae_mapping_row["output_name"] in siae_constants.SIAE_LEGAL_FORM_CHOICE_LIST:
                        results["success"] += 1
                        if not options["dry_run"]:
                            Siae.objects.filter(id=siae.id).update(legal_form=siae_mapping_row["output_name"])
                    else:
                        results["error"] += 1
                        self.stdout_error(f"unknown output_name {siae_mapping_row['output_name']}")
                else:
                    results["error"] += 1
                    self.stdout_error(f"unknown input_name {siae.api_entreprise_forme_juridique}")
            progress += 1
            if (progress % 1000) == 0:
                self.stdout_info(f"{progress}...")

        self.stdout_info("-" * 80)
        self.stdout_info("RECAP")
        self.stdout_info(f"SIAE count: {siaes.count()}")
        self.stdout_info(f"Success count: {results['success']}")
        self.stdout_info(f"Error count: {results['error']}")
