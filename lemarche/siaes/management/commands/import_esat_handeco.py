import csv
import os
import time
from xml.etree import ElementTree

from django.core.management.base import BaseCommand
from django.utils import timezone

from lemarche.sectors.models import Sector
from lemarche.siaes.constants import department_from_postcode
from lemarche.siaes.models import Siae
from lemarche.utils.apis.api_entreprise import etablissement_get_or_error  # exercice_get_or_error
from lemarche.utils.apis.geocoding import get_geocoding_data
from lemarche.utils.data import rename_dict_key, reset_app_sql_sequences


FILE_NAME = "esat_handeco.xml"
FILE_PATH = os.path.dirname(os.path.realpath(__file__)) + "/" + FILE_NAME
FIELD_NAME_LIST = [
    "title",
    "siret",
    "zip",
    "city",
    "region",
    "phone",
    "mail",
    "effectif",
    "type",
    # "secteurs",
    # dateupdate
]


SECTORS_DICT = {}
SECTORS_MAPPING_CSV_PATH = os.path.dirname(os.path.realpath(__file__)) + "/handeco_sectors_mapping.csv"
SOURCE_COLUMN_NAME = "Secteur Handeco"
MARCHE_COLUMN_NAMES = ["Secteur Marche 1", "Secteur Marche 2"]
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


def read_xml():
    print("Reading XML file...")
    esat_list = []

    data_file = os.path.abspath(FILE_PATH)
    xml_tree = ElementTree.parse(data_file)
    xml_root = xml_tree.getroot()

    for xml_elt in xml_root.findall("structure"):
        esat = {}
        for field in FIELD_NAME_LIST:
            try:
                esat[field] = xml_elt.find(field).text
            except:  # noqa
                esat[field] = ""
        esat["secteurs"] = []
        esat_sectors = xml_elt.find("secteurs")
        for esat_sector in esat_sectors.findall("secteur"):
            esat["secteurs"].append(
                {"secteurnom": esat_sector.find("secteurnom").text, "activite": esat_sector.find("activite").text}
            )
        esat_list.append(esat)

    return esat_list


class Command(BaseCommand):
    """
    The source file is a .xml
    We transform each Siae to a dict for easier processing

    Usage: poetry run python manage.py import_esat_handeco
    """

    def handle(self, *args, **options):
        print("-" * 80)
        reset_app_sql_sequences("siaes")
        esat_list = read_xml()

        old_esat_count = Siae.objects.filter(kind=Siae.KIND_ESAT).count()

        print("Importing Handeco (after GESAT)...")
        progress = 0
        for esat in esat_list:
            if Siae.objects.filter(siret=esat["siret"]).exists():
                print(
                    f"SIRET already exists skipping,{Siae.objects.filter(siret=esat['siret']).count()},{esat['title']},{esat['siret']},{Siae.objects.filter(siret=esat['siret']).first().name}"  # noqa
                )
            else:
                progress += 1
                if (progress % 50) == 0:
                    print(f"{progress}...")
                self.import_esat(esat)
        # self.import_esat(esat_list[0])

        new_esat_count = Siae.objects.filter(kind=Siae.KIND_ESAT).count()

        print(f"Imported {new_esat_count - old_esat_count} additional ESAT siaes !")

    def import_esat(self, esat):  # noqa C901
        # store raw dict
        esat["import_source"] = "esat_handeco"
        esat["import_raw_object"] = esat.copy()

        # defaults
        esat["kind"] = Siae.KIND_ESAT
        esat["source"] = Siae.SOURCE_ESAT
        esat["geo_range"] = Siae.GEO_RANGE_DEPARTMENT

        # basic fields
        rename_dict_key(esat, "title", "name")
        esat["name"].strip().replace("  ", " ")
        if "siret" in esat:
            esat["siret_is_valid"] = True

        # contact fields
        rename_dict_key(esat, "mail", "email")
        esat["contact_phone"] = esat["phone"]
        esat["contact_email"] = esat["email"]

        # geo fields
        rename_dict_key(esat, "zip", "post_code")
        if "post_code" in esat:
            esat["post_code"] = esat["post_code"].replace(" ", "")  # sometimes formated '12 345'
            esat["department"] = department_from_postcode(esat["post_code"])
        esat["city"] = esat["city"].strip()  # space at the beginning
        esat["region"] = esat["region"].strip()  # just to be sure
        # manually fix region="DOM"

        # enrich with geocoding
        geocoding_data = get_geocoding_data(esat["city"], post_code=esat["post_code"])
        if geocoding_data:
            if esat["post_code"] != geocoding_data["post_code"]:
                if esat["post_code"][:2] == geocoding_data["post_code"][:2]:
                    # update post_code as well
                    esat["city"] = geocoding_data["city"]  # avoid uppercase
                    esat["coords"] = geocoding_data["coords"]
                    esat["post_code"] = geocoding_data["post_code"]
                else:
                    print(
                        f"Geocoding found a different place,{esat['name']},{esat['post_code']},{geocoding_data['post_code']}"  # noqa
                    )
            else:
                esat["city"] = geocoding_data["city"]  # avoid uppercase
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
            esat["ig_employees"] = etablissement["employees"]
            if etablissement["date_constitution"]:
                esat["ig_date_constitution"] = timezone.make_aware(etablissement["date_constitution"])
        # else:
        #     print(error)
        # TODO: if 404, siret_is_valid = False
        # exercice, error = exercice_get_or_error(esat["siret"], reason="Mise à jour donnéés Marché de la plateforme de l'Inclusion")  # noqa
        # if exercice:
        #     esat["ig_ca"] = exercice["ca"]
        # # else:
        # #     print(error)

        # sectors
        esat_sectors = []
        for domaine in esat["secteurs"]:
            esat_sectors.extend(SECTORS_DICT.get(domaine["secteurnom"], []))

        # cleanup unused fields
        [esat.pop(key) for key in ["type", "effectif", "secteurs", "import_source"]]

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
