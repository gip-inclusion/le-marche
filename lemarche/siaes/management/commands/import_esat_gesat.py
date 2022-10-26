import csv
import os
import re
import time

from django.core.management.base import BaseCommand
from django.utils import timezone

from lemarche.sectors.models import Sector
from lemarche.siaes import constants as siae_constants
from lemarche.siaes.constants import department_from_postcode
from lemarche.siaes.models import Siae
from lemarche.utils.apis.api_entreprise import etablissement_get_or_error  # exercice_get_or_error
from lemarche.utils.apis.geocoding import get_geocoding_data
from lemarche.utils.data import rename_dict_key, reset_app_sql_sequences


FILE_NAME = "esat_gesat_2.csv"
FILE_PATH = os.path.dirname(os.path.realpath(__file__)) + "/" + FILE_NAME
FIELD_NAME_LIST = [
    "Raison Sociale",
    "Adresse",
    "Lieudit/BP",
    "Code Postal",
    "Ville",
    "Région",
    "Tel",
    "Email",
    "Siret",
    "Date d'ouverture",
    "Denière date de MAJ",
    "Capacité d'accueil (nombre de TH total)",
    "Pôles de compétences",
    "Domaine 1",  # ... Domaine 13
]


SECTORS_DICT = {}
SECTORS_MAPPING_CSV_PATH = os.path.dirname(os.path.realpath(__file__)) + "/gesat_sectors_mapping.csv"
SOURCE_COLUMN_NAME = "Secteur Gesat"
MARCHE_COLUMN_NAMES = ["Secteur Marche 1", "Secteur Marche 2", "Secteur Marche 3"]
with open(SECTORS_MAPPING_CSV_PATH) as csv_file:
    csvreader = csv.DictReader(csv_file, delimiter=",")
    for index, row in enumerate(csvreader):
        SECTORS_DICT[row[SOURCE_COLUMN_NAME]] = []
        for column in MARCHE_COLUMN_NAMES:
            if row[column]:
                try:
                    if row[column].startswith("Autre"):
                        sector_group_name = row[column].split("(")[1][:-1]
                        sector = Sector.objects.get(name="Autre", group__name=sector_group_name)
                    else:
                        sector = Sector.objects.get(name=row[column])
                    SECTORS_DICT[row[SOURCE_COLUMN_NAME]].append(sector.id)
                except:  # noqa
                    print("error or missing sector", row[column])


def read_csv():
    esat_list = list()

    with open(FILE_PATH) as csv_file:
        csvreader = csv.DictReader(csv_file, delimiter=",")
        for index, row in enumerate(csvreader):
            esat_sectors_string = row["Pôles de compétences"]
            esat_sectors_list = re.findall("[A-Z][^A-Z]*", esat_sectors_string)

            row["Pôles de compétences list"] = list()
            for esat_sector in esat_sectors_list:
                if esat_sector.endswith(", "):
                    esat_sector = esat_sector[:-2]
                row["Pôles de compétences list"].append(esat_sector)
            row.pop("Pôles de compétences")

            row["Domaines list"] = list()
            for i in range(1, 13 + 1):
                if row[f"Domaine {i}"]:
                    row["Domaines list"].append(row[f"Domaine {i}"])
            [row.pop(key) for key in [f"Domaine {i}" for i in range(1, 13 + 1)]]

            esat_list.append(row)

    return esat_list


def extract_domaine_set(esat_list):
    domaine_set = set()
    for esat in esat_list:
        for domaine in esat["Domaines list"]:
            if domaine:
                domaine_set.add(domaine)

    print(len(domaine_set))
    for domaine in sorted(domaine_set):
        print(domaine)


def extract_duplicates(esat_list):
    esat_siret_list = list()
    for esat in esat_list:
        rename_dict_key(esat, "Raison Sociale", "name")
        rename_dict_key(esat, "Siret", "siret")
        if "siret" in esat:
            esat["siret"] = esat["siret"].replace(" ", "")
        esat_siret_index = next(
            (index for (index, s) in enumerate(esat_siret_list) if s["siret"] == esat["siret"]), None
        )
        if esat_siret_index is None:
            esat_siret_list.append({"name": esat["name"], "siret": esat["siret"]})
        else:
            print("===========")
            print("Current", esat["name"], esat["siret"])
            print("Duplicate", esat_siret_list[esat_siret_index]["name"], esat_siret_list[esat_siret_index]["siret"])


class Command(BaseCommand):
    """
    Usage: poetry run python manage.py import_esat_gesat
    """

    def handle(self, *args, **options):
        print("-" * 80)
        Siae.objects.filter(kind=siae_constants.KIND_ESAT).delete()
        reset_app_sql_sequences("siaes")
        esat_list = read_csv()

        # extract_domaine_set(esat_list)
        # extract_duplicates(esat_list)

        print("Importing GESAT...")
        progress = 0
        for index, esat in enumerate(esat_list):
            progress += 1
            if (progress % 50) == 0:
                print(f"{progress}...")
            self.import_esat(esat)

    def import_esat(self, esat):  # noqa C901
        # store raw dict
        esat["import_source"] = "esat_gesat"
        esat["import_raw_object"] = esat.copy()

        # defaults
        esat["kind"] = siae_constants.KIND_ESAT
        esat["source"] = Siae.SOURCE_ESAT
        esat["geo_range"] = Siae.GEO_RANGE_DEPARTMENT

        # basic fields
        rename_dict_key(esat, "Raison Sociale", "name")
        esat["name"].strip()
        esat["name"] = esat["name"].replace("  ", " ")
        rename_dict_key(esat, "Siret", "siret")
        if "siret" in esat:
            esat["siret"] = esat["siret"].replace(" ", "")
            esat["siret_is_valid"] = True

        # contact fields
        rename_dict_key(esat, "Email", "email")
        rename_dict_key(esat, "Tel", "phone")
        esat["phone"].strip()
        esat["contact_email"] = esat["email"]
        esat["contact_phone"] = esat["phone"]

        # geo fields
        rename_dict_key(esat, "Adresse", "address")
        rename_dict_key(esat, "Code Postal", "post_code")
        if "post_code" in esat:
            esat["post_code"] = esat["post_code"].replace(" ", "")
            esat["department"] = department_from_postcode(esat["post_code"])
        rename_dict_key(esat, "Ville", "city")
        rename_dict_key(esat, "Région", "region")
        esat["region"].strip()
        # manually fix some regions

        # enrich with geocoding
        geocoding_data = get_geocoding_data(esat["address"] + " " + esat["city"], post_code=esat["post_code"])
        if geocoding_data:
            if esat["post_code"] != geocoding_data["post_code"]:
                if esat["post_code"][:2] == geocoding_data["post_code"][:2]:
                    # update post_code as well
                    esat["coords"] = geocoding_data["coords"]
                    esat["post_code"] = geocoding_data["post_code"]
                else:
                    print(
                        f"Geocoding found a different place,{esat['name']},{esat['post_code']},{geocoding_data['post_code']}"  # noqa
                    )
            else:
                esat["coords"] = geocoding_data["coords"]
        else:
            print(f"Geocoding not found,{esat['name']},{esat['post_code']}")

        # enrich with API Entreprise
        etablissement, error = etablissement_get_or_error(
            esat["siret"], reason="Mise à jour donnéés Marché de la plateforme de l'Inclusion"
        )
        if etablissement:
            esat["nature"] = Siae.NATURE_HEAD_OFFICE if etablissement["is_head_office"] else Siae.NATURE_ANTENNA
            # esat["is_active"] = False if not etablissement["is_closed"] else True
            esat["api_entreprise_employees"] = etablissement["employees"]
            if etablissement["date_constitution"]:
                esat["api_entreprise_date_constitution"] = timezone.make_aware(etablissement["date_constitution"])
        # else:
        #     print(error)
        # TODO: if 404, siret_is_valid = False
        # exercice, error = exercice_get_or_error(esat["siret"], reason="Mise à jour donnéés Marché de la plateforme de l'Inclusion")  # noqa
        # if exercice:
        #     esat["api_entreprise_ca"] = exercice["ca"]
        # # else:
        # #     print(error)

        # sectors
        esat_sectors = []
        for domaine in esat["Domaines list"]:
            esat_sectors.extend(SECTORS_DICT.get(domaine, []))

        # dates
        [esat.pop(key) for key in ["Date d'ouverture", "Denière date de MAJ"]]

        # cleanup unused fields
        [esat.pop(key) for key in ["Domaines list", "Pôles de compétences list", "import_source"]]
        [esat.pop(key) for key in ["Lieudit/BP", "Capacité d'accueil (nombre de TH total)"]]

        # create object
        try:
            siae = Siae.objects.create(**esat)
            siae.sectors.set(esat_sectors)
            # print("ESAT ajoutée", siae.name)
        except Exception as e:
            print(e)
            print(esat)

        # avoid DDOSing APIs
        time.sleep(0.1)
