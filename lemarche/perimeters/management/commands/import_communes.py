# https://github.com/betagouv/itou/blob/master/itou/cities/management/commands/import_cities.py

import json
import logging
import os

from django.contrib.gis.geos import GEOSGeometry
from django.core.management.base import BaseCommand

from lemarche.perimeters.models import Perimeter
from lemarche.utils.constants import (
    DEPARTMENT_TO_REGION,
    DEPARTMENTS,
    REGIONS,
    department_from_postcode,
    get_region_code_from_name,
)


CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))

# Use the data generated by `django-admin generate_communes`.
CITIES_JSON_FILE = f"{CURRENT_DIR}/data/communes.json"

# TODO: add missing coordinates
MISSING_COORDS = {
    ("Miquelon-Langlade", "97501"): {
        "codeDepartement": "975",
        "codeRegion": "97",
        "coordinates": {"type": "Point", "coordinates": [-56.379167, 47.1]},
    },
    ("Saint-Pierre", "97502"): {
        "codeDepartement": "975",
        "codeRegion": "97",
        "coordinates": {"type": "Point", "coordinates": [55.4778, -21.3419]},
    },
    ("Saint-Barthélemy", "97701"): {
        "codeDepartement": "977",
        "codeRegion": "97",
        "coordinates": {"type": "Point", "coordinates": [-62.8342438, 17.897728]},
    },
    ("Saint-Martin", "97801"): {
        "codeDepartement": "978",
        "codeRegion": "97",
        "coordinates": {"type": "Point", "coordinates": [-63.0668, 18.0603]},
    },
    ("Îles Saint-Paul et Nouvelle-Amsterdam", "98411"): {
        "codeDepartement": "984",
        "codeRegion": "97",
        "coordinates": None,
    },
    ("Archipel des Kerguelen", "98412"): {"codeDepartement": "984", "codeRegion": "97", "coordinates": None},
    ("Archipel des Crozet", "98413"): {"codeDepartement": "984", "codeRegion": "97", "coordinates": None},
    ("La Terre-Adélie", "98414"): {"codeDepartement": "984", "codeRegion": "97", "coordinates": None},
    ("Îles Éparses de l'océan Indien", "98415"): {"codeDepartement": "984", "codeRegion": "97", "coordinates": None},
    ("Alo", "98611"): {"codeDepartement": "986", "codeRegion": "97", "coordinates": None},
    ("Sigave", "98612"): {"codeDepartement": "986", "codeRegion": "97", "coordinates": None},
    ("Uvea", "98613"): {"codeDepartement": "986", "codeRegion": "97", "coordinates": None},
    ("Anaa", "98711"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Arue", "98712"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Arutua", "98713"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Bora-Bora", "98714"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Faaa", "98715"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Fakarava", "98716"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Fangatau", "98717"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Fatu-Hiva", "98718"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Gambier", "98719"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Hao", "98720"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Hikueru", "98721"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Hitiaa O Te Ra", "98722"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Hiva-Oa", "98723"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Huahine", "98724"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Mahina", "98725"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Makemo", "98726"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Manihi", "98727"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Maupiti", "98728"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Moorea-Maiao", "98729"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Napuka", "98730"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Nuku-Hiva", "98731"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Nukutavake", "98732"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Paea", "98733"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Papara", "98734"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Papeete", "98735"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Pirae", "98736"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Pukapuka", "98737"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Punaauia", "98738"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Raivavae", "98739"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Rangiroa", "98740"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Rapa", "98741"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Reao", "98742"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Rimatara", "98743"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Rurutu", "98744"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Tahaa", "98745"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Tahuata", "98746"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Taiarapu-Est", "98747"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Taiarapu-Ouest", "98748"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Takaroa", "98749"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Taputapuatea", "98750"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Tatakoto", "98751"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Teva I Uta", "98752"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Tubuai", "98753"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Tumaraa", "98754"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Tureia", "98755"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Ua-Huka", "98756"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Ua-Pou", "98757"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Uturoa", "98758"): {"codeDepartement": "987", "codeRegion": "97", "coordinates": None},
    ("Belep", "98801"): {"codeDepartement": "988", "codeRegion": "97", "coordinates": None},
    ("Bouloupari", "98802"): {"codeDepartement": "988", "codeRegion": "97", "coordinates": None},
    ("Bourail", "98803"): {"codeDepartement": "988", "codeRegion": "97", "coordinates": None},
    ("Canala", "98804"): {"codeDepartement": "988", "codeRegion": "97", "coordinates": None},
    ("Dumbéa", "98805"): {"codeDepartement": "988", "codeRegion": "97", "coordinates": None},
    ("Farino", "98806"): {"codeDepartement": "988", "codeRegion": "97", "coordinates": None},
    ("Hienghène", "98807"): {"codeDepartement": "988", "codeRegion": "97", "coordinates": None},
    ("Houaïlou", "98808"): {"codeDepartement": "988", "codeRegion": "97", "coordinates": None},
    ("L'Île-des-Pins", "98809"): {"codeDepartement": "988", "codeRegion": "97", "coordinates": None},
    ("Kaala-Gomen", "98810"): {"codeDepartement": "988", "codeRegion": "97", "coordinates": None},
    ("Koné", "98811"): {"codeDepartement": "988", "codeRegion": "97", "coordinates": None},
    ("Koumac", "98812"): {"codeDepartement": "988", "codeRegion": "97", "coordinates": None},
    ("La Foa", "98813"): {"codeDepartement": "988", "codeRegion": "97", "coordinates": None},
    ("Lifou", "98814"): {"codeDepartement": "988", "codeRegion": "97", "coordinates": None},
    ("Maré", "98815"): {"codeDepartement": "988", "codeRegion": "97", "coordinates": None},
    ("Moindou", "98816"): {"codeDepartement": "988", "codeRegion": "97", "coordinates": None},
    ("Le Mont-Dore", "98817"): {"codeDepartement": "988", "codeRegion": "97", "coordinates": None},
    ("Nouméa", "98818"): {"codeDepartement": "988", "codeRegion": "97", "coordinates": None},
    ("Ouégoa", "98819"): {"codeDepartement": "988", "codeRegion": "97", "coordinates": None},
    ("Ouvéa", "98820"): {"codeDepartement": "988", "codeRegion": "97", "coordinates": None},
    ("Païta", "98821"): {"codeDepartement": "988", "codeRegion": "97", "coordinates": None},
    ("Poindimié", "98822"): {"codeDepartement": "988", "codeRegion": "97", "coordinates": None},
    ("Ponérihouen", "98823"): {"codeDepartement": "988", "codeRegion": "97", "coordinates": None},
    ("Pouébo", "98824"): {"codeDepartement": "988", "codeRegion": "97", "coordinates": None},
    ("Pouembout", "98825"): {"codeDepartement": "988", "codeRegion": "97", "coordinates": None},
    ("Poum", "98826"): {"codeDepartement": "988", "codeRegion": "97", "coordinates": None},
    ("Poya", "98827"): {"codeDepartement": "988", "codeRegion": "97", "coordinates": None},
    ("Sarraméa", "98828"): {"codeDepartement": "988", "codeRegion": "97", "coordinates": None},
    ("Thio", "98829"): {"codeDepartement": "988", "codeRegion": "97", "coordinates": None},
    ("Touho", "98830"): {"codeDepartement": "988", "codeRegion": "97", "coordinates": None},
    ("Voh", "98831"): {"codeDepartement": "988", "codeRegion": "97", "coordinates": None},
    ("Yaté", "98832"): {"codeDepartement": "988", "codeRegion": "97", "coordinates": None},
    ("Kouaoua", "98833"): {"codeDepartement": "988", "codeRegion": "97", "coordinates": None},
    ("Île de Clipperton", "98901"): {"codeDepartement": "989", "codeRegion": "97", "coordinates": None},
}


class Command(BaseCommand):
    """
    Import French cities data from a JSON file into the database.

    To debug:
        django-admin import_communes --dry-run
        django-admin import_communes --dry-run --verbosity=2

    To populate the database:
        django-admin import_communes
    """

    help = "Import the content of the French cities JSON file into the database."

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
        self.stdout.write("Importing Perimeters > communes...")
        self.stdout.write(
            f"Before: {Perimeter.objects.filter(kind=Perimeter.KIND_CITY).count()} {Perimeter.KIND_CITY}s"
        )

        self.set_logger(options.get("verbosity"))

        with open(CITIES_JSON_FILE, "r") as raw_json_data:
            json_data = json.load(raw_json_data)
            total_len = len(json_data)
            last_progress = 0

            for i, item in enumerate(json_data):
                progress = int((100 * i) / total_len)
                if progress > last_progress + 5:
                    self.stdout.write(f"Creating cities… {progress}%")
                    last_progress = progress

                name = item["nom"]
                insee_code = item["code"]

                post_codes = item["codesPostaux"]
                department_code = item.get("codeDepartement")
                region_code = item.get("codeRegion")
                population = item.get("population")

                if not department_code:
                    # Sometimes department is missing. We get it from the postcode.
                    if not post_codes:
                        self.stderr.write(f"No department for {name}. Trying with insee_code")
                        post_codes = [insee_code]
                    department_code = department_from_postcode(post_codes[0])

                assert department_code in DEPARTMENTS

                if not region_code:
                    # Sometimes region is missing. We get it from the department_code.
                    region_name = DEPARTMENT_TO_REGION[department_code]
                    region_code = get_region_code_from_name(region_name)

                assert region_code in REGIONS

                coords = item.get("centre")

                # Add coords of cities for which API GEO has no data.
                if not coords and (name, insee_code) in MISSING_COORDS:
                    department_code = MISSING_COORDS[(name, insee_code)]["codeDepartement"]
                    region_code = MISSING_COORDS[(name, insee_code)]["codeRegion"]
                    coords = MISSING_COORDS[(name, insee_code)]["coordinates"]

                if coords:
                    coords = GEOSGeometry(f"{coords}")  # Feed `GEOSGeometry` with GeoJSON.
                else:
                    self.stderr.write(f"No coordinates for {name}. Skipping…")
                    # continue

                self.logger.debug("-" * 80)
                self.logger.debug(name)
                self.logger.debug(post_codes)
                self.logger.debug(insee_code)
                self.logger.debug(department_code)
                self.logger.debug(coords)

                if not dry_run:
                    Perimeter.objects.update_or_create(
                        kind=Perimeter.KIND_CITY,
                        name=name,
                        insee_code=insee_code,
                        post_codes=post_codes,
                        department_code=department_code,
                        region_code=region_code,
                        population=population,
                        defaults={
                            "coords": coords,
                        },
                    )

        self.stdout.write("Done.")
        self.stdout.write(
            f"After: {Perimeter.objects.filter(kind=Perimeter.KIND_CITY).count()} {Perimeter.KIND_CITY}s"
        )
