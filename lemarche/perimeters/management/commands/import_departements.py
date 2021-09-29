import json
import logging
import os

from django.core.management.base import BaseCommand
from django.template.defaultfilters import slugify

from lemarche.perimeters.models import Perimeter
from lemarche.siaes.constants import DEPARTMENTS, REGIONS_WITH_CODES


CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))

DEPARTMENTS_JSON_FILE = f"{CURRENT_DIR}/data/departements.json"


class Command(BaseCommand):
    """
    Import French departments data from a JSON file into the database.

    To debug:
        django-admin import_departements --dry-run
        django-admin import_departements --dry-run --verbosity=2

    To populate the database:
        django-admin import_departements
    """

    help = "Import the content of the French departments JSON file into the database."

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

        self.set_logger(options.get("verbosity"))

        with open(DEPARTMENTS_JSON_FILE, "r") as raw_json_data:

            json_data = json.load(raw_json_data)

            for i, item in enumerate(json_data):

                name = item["nom"]
                kind = Perimeter.KIND_DEPARTMENT
                insee_code = item["code"]

                region_code = item.get("codeRegion")

                assert insee_code in DEPARTMENTS
                assert region_code in REGIONS_WITH_CODES

                slug = slugify(name)

                self.logger.debug("-" * 80)
                self.logger.debug(name)
                self.logger.debug(slug)
                self.logger.debug(insee_code)

                if not dry_run:
                    Perimeter.objects.update_or_create(
                        slug=slug,
                        kind=kind,
                        defaults={
                            "name": name,
                            "insee_code": insee_code,
                            "region_code": region_code,
                        },
                    )

        # Also add 'Collectivités d'outre-mer'
        # https://fr.wikipedia.org/wiki/Collectivit%C3%A9_d%27outre-mer
        # https://www.insee.fr/fr/information/2028040
        if not dry_run:
            MISSING_DEPARTMENTS = [
                {"nom": "Saint-Pierre-et-Miquelon", "code": "975", "codeRegion": "97"},
                {"nom": "Saint-Barthélemy", "code": "977", "codeRegion": "97"},
                {"nom": "Saint-Martin", "code": "978", "codeRegion": "97"},
                {"nom": "Terres australes et antarctiques françaises", "code": "984", "codeRegion": "97"},
                {"nom": "Wallis-et-Futuna", "code": "986", "codeRegion": "97"},
                {"nom": "Polynésie française", "code": "987", "codeRegion": "97"},
                {"nom": "Nouvelle-Calédonie", "code": "988", "codeRegion": "97"},
                {"nom": "Île de Clipperton", "code": "989", "codeRegion": "97"},
            ]
            for department in MISSING_DEPARTMENTS:
                name = department["nom"]
                kind = Perimeter.KIND_DEPARTMENT
                insee_code = department["code"]
                region_code = department["codeRegion"]

                slug = slugify(name)

                Perimeter.objects.update_or_create(
                    slug=slug,
                    kind=kind,
                    defaults={
                        "name": name,
                        "insee_code": insee_code,
                        "region_code": region_code,
                    },
                )

        self.stdout.write("-" * 80)
        self.stdout.write("Done.")
