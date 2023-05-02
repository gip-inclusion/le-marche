import csv
import os
import time

from django.core.management.base import BaseCommand

from lemarche.sectors.models import Sector
from lemarche.siaes import constants as siae_constants
from lemarche.siaes.models import Siae
from lemarche.siaes.validators import validate_siret
from lemarche.utils.apis.geocoding import get_geocoding_data
from lemarche.utils.constants import DEPARTMENT_TO_REGION, department_from_postcode
from lemarche.utils.data import rename_dict_key, reset_app_sql_sequences


SEP_FILE_NAME = "sep.csv"
SEP_FILE_PATH = os.path.dirname(os.path.realpath(__file__)) + "/" + SEP_FILE_NAME
SEP_EXTERNE_FILE_NAME = "sep_externe.csv"
SEP_EXTERNE_FILE_PATH = os.path.dirname(os.path.realpath(__file__)) + "/" + SEP_EXTERNE_FILE_NAME

SECTOR_COLUMN_NAME_LIST = ["Secteurs d'act 1", "Secteurs d'act 2", "Secteurs d'act 3"]
USER_COLUMN_NAME_LIST = ["Nom", "Prénom", "Email"]
PRESTA_TYPE_NAME_LIST = ["Type de prestation 1", "Type de prestation 2"]
PRESTA_TYPE_MAPPING = {
    "Prestation de services": siae_constants.PRESTA_PREST,
    "Fabrication et commercialisation de biens": siae_constants.PRESTA_BUILD,
}


def read_csv(file_path):
    siae_list = list()

    with open(file_path) as csv_file:
        csvreader = csv.DictReader(csv_file, delimiter=",")
        for index, row in enumerate(csvreader):

            # sectors
            row["Secteurs d'act list"] = list()
            for sector_column_name in SECTOR_COLUMN_NAME_LIST:
                if row[sector_column_name]:
                    Sector.objects.get(name=row[sector_column_name])
                    row["Secteurs d'act list"].append(row[sector_column_name])

            # users
            row["Gestionnaires"] = list()
            for i in range(1, 3):
                user = dict()
                for user_column_name in USER_COLUMN_NAME_LIST:
                    user_column_name_with_range = f"{user_column_name} {i}"
                    if user_column_name_with_range in row:
                        if row[user_column_name_with_range]:
                            user[user_column_name] = row[f"{user_column_name} {i}"]
                if len(user) > 0:
                    row["Gestionnaires"].append(user)

            siae_list.append(row)

    return siae_list


class Command(BaseCommand):
    """
    Usage: poetry run python manage.py import_sep
    """

    def handle(self, *args, **options):
        print("-" * 80)
        Siae.objects.filter(kind=siae_constants.KIND_SEP).delete()
        reset_app_sql_sequences("siaes")

        print("Importing SEP...")
        siae_list = read_csv(SEP_FILE_PATH)
        progress = 0
        for index, siae in enumerate(siae_list):
            progress += 1
            if (progress % 10) == 0:
                print(f"{progress}...")
            self.import_sep(siae, source="sep")

        print("Importing SEP Externe...")
        siae_list = read_csv(SEP_EXTERNE_FILE_PATH)
        progress = 0
        for index, siae in enumerate(siae_list):
            progress += 1
            if (progress % 10) == 0:
                print(f"{progress}...")
            self.import_sep(siae, source="sep_externe")

        print("Done !")
        print(f"Imported {Siae.objects.filter(kind=siae_constants.KIND_SEP).count()} SIAE")

    def import_sep(self, siae, source="sep"):  # noqa C901
        # store raw dict
        siae["import_source"] = source
        siae["import_raw_object"] = siae.copy()

        # defaults
        siae["kind"] = siae_constants.KIND_SEP
        siae["source"] = siae_constants.KIND_SEP
        siae["geo_range"] = Siae.GEO_RANGE_DEPARTMENT

        # basic fields
        rename_dict_key(siae, "Raison sociale", "name")
        siae["name"].strip()
        rename_dict_key(siae, "Enseigne", "brand")
        rename_dict_key(siae, "Siret", "siret")
        if "siret" in siae:
            siae["siret"].strip()
            siae["siret"] = siae["siret"].replace(" ", "").replace(" ", "")
            if validate_siret(siae["siret"]):
                siae["siret_is_valid"] = True

        # presta_type
        siae["presta_type"] = list()
        for presta_type_name in PRESTA_TYPE_NAME_LIST:
            if presta_type_name in siae:
                if siae[presta_type_name]:
                    siae["presta_type"].append(PRESTA_TYPE_MAPPING[siae[presta_type_name]])

        # contact fields
        rename_dict_key(siae, "Prénom 1", "contact_first_name")
        rename_dict_key(siae, "Nom 1", "contact_last_name")
        rename_dict_key(siae, "Site internet", "website")
        siae["contact_website"] = siae["website"]
        rename_dict_key(siae, "Email 1", "email")
        siae["contact_email"] = siae["email"]
        rename_dict_key(siae, "Téléphone", "phone")
        siae["phone"].strip()
        siae["contact_phone"] = siae["phone"]

        # geo fields
        rename_dict_key(siae, "Adresse", "address")
        rename_dict_key(siae, "Code Postal", "post_code")
        if "post_code" in siae:
            siae["department"] = department_from_postcode(siae["post_code"])
            siae["region"] = DEPARTMENT_TO_REGION[siae["department"]]
        rename_dict_key(siae, "Ville", "city")

        # enrich with geocoding
        geocoding_data = get_geocoding_data(siae["address"] + " " + siae["city"], post_code=siae["post_code"])
        if geocoding_data:
            if siae["post_code"] != geocoding_data["post_code"]:
                if siae["post_code"][:2] == geocoding_data["post_code"][:2]:
                    # update post_code as well
                    siae["coords"] = geocoding_data["coords"]
                    siae["post_code"] = geocoding_data["post_code"]
                else:
                    print(
                        f"Geocoding found a different place,{siae['name']},{siae['post_code']},{geocoding_data['post_code']}"  # noqa
                    )
            else:
                siae["coords"] = geocoding_data["coords"]
        else:
            print(f"Geocoding not found,{siae['name']},{siae['post_code']}")

        # enrich with API Entreprise, API QPV, API ZRR?
        # done in weekly CRON job

        # sectors
        siae_sectors = []
        for sector_name in siae["Secteurs d'act list"]:
            sector = Sector.objects.get(name=sector_name)
            siae_sectors.append(sector)

        # cleanup unused fields
        [siae.pop(key) for key in ["Secteurs d'act list", "Gestionnaires", "import_source"]]  # temporary fields
        [siae.pop(key) for key in ["Type de structure", "Département", "Région", "Périmètre d'intervention"]]
        [
            siae.pop(key)
            for key in [
                "Prénom de l'utilisateur principal",
                "Nom 2",
                "Prénom 2",
                "Email 2",
                "Nom 3",
                "Prénom 3",
                "Email 3",
            ]
            if key in siae
        ]
        [
            siae.pop(key)
            for key in [
                "Logo",
                "nombre de salariés",
                "nombre d'opérateurs",
                "Date de création",
                "Ouvert à la co-traitance ?",
                "Liste des labels",
                "Liste des réseaux",
            ]
        ]
        [siae.pop(key) for key in SECTOR_COLUMN_NAME_LIST if key in siae]
        [siae.pop(key) for key in PRESTA_TYPE_NAME_LIST if key in siae]

        # create object
        try:
            siae = Siae.objects.create(**siae)
            siae.sectors.set(siae_sectors)
            # print("ESAT ajoutée", siae.name)
        except Exception as e:
            print(e)
            print(siae)

        # avoid DDOSing APIs
        time.sleep(0.1)
