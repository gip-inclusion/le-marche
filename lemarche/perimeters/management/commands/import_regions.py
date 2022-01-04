import json
import logging
import os

from django.core.management.base import BaseCommand

from lemarche.perimeters.models import Perimeter
from lemarche.siaes.constants import REGIONS


CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))

REGIONS_JSON_FILE = f"{CURRENT_DIR}/data/regions.json"


class Command(BaseCommand):
    """
    Import French regions data from a JSON file into the database.

    To debug:
        django-admin import_regions --dry-run
        django-admin import_regions --dry-run --verbosity=2

    To populate the database:
        django-admin import_regions
    """

    help = "Import the content of the French regions JSON file into the database."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Only print data to import")

    def set_logger(self, verbosity):
        """
        Set logger level based on the verbosity option.
        """
        handler = logging.StreamHandler(self.stdout)

        self.logger = logging.getLogger(__name__)
        self.logger.propagate = False
        self.logger.addHandler(handler)

        self.logger.setLevel(logging.INFO)
        if verbosity > 1:
            self.logger.setLevel(logging.DEBUG)

    def handle(self, dry_run=False, **options):
        self.stdout.write("-" * 80)
        self.stdout.write("Importing Perimeters > regions...")
        self.stdout.write(
            f"Before: {Perimeter.objects.filter(kind=Perimeter.KIND_REGION).count()} {Perimeter.KIND_REGION}s"
        )

        self.set_logger(options.get("verbosity"))

        with open(REGIONS_JSON_FILE, "r") as raw_json_data:

            json_data = json.load(raw_json_data)

            for i, item in enumerate(json_data):

                name = item["nom"]
                insee_code = item["code"]

                assert insee_code in REGIONS

                # Important! We need to prefix the regions' insee_code to avoid conflicts with departments
                insee_code = f"R{insee_code}"

                # Note: some regions have the same name as a department
                # managed in Perimeter.set_slug method

                self.logger.debug("-" * 80)
                self.logger.debug(name)
                self.logger.debug(insee_code)

                if not dry_run:
                    Perimeter.objects.get_or_create(
                        kind=Perimeter.KIND_REGION,
                        name=name,
                        insee_code=insee_code,
                    )

        # Also add 'Collectivités d'outre-mer'
        # https://fr.wikipedia.org/wiki/Collectivit%C3%A9_d%27outre-mer
        name = "Collectivités d'outre-mer"
        insee_code = "R97"

        if not dry_run:
            Perimeter.objects.get_or_create(
                kind=Perimeter.KIND_REGION,
                name=name,
                insee_code=insee_code,
            )

        self.stdout.write("Done.")
        self.stdout.write(
            f"After: {Perimeter.objects.filter(kind=Perimeter.KIND_REGION).count()} {Perimeter.KIND_REGION}s"
        )
