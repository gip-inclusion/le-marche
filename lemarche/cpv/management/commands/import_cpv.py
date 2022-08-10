import os
from xml.etree import ElementTree

from django.core.management.base import BaseCommand

from lemarche.cpv.models import Code
from lemarche.utils.data import reset_app_sql_sequences


FILE_NAME = "cpv_2008.xml"
# FILE_NAME = "../itou_ressources/features/cpv/cpv_2008_xml/cpv_2008.xml"
FILE_PATH = os.path.dirname(os.path.realpath(__file__)) + "/" + FILE_NAME


def read_xml():
    print("-" * 80)
    print("Reading XML file...")
    cpv_list = []

    data_file = os.path.abspath(FILE_PATH)
    xml_tree = ElementTree.parse(data_file)
    xml_root = xml_tree.getroot()

    for xml_elt in xml_root.findall("CPV"):
        cpv = {}

        # code
        cpv_code_raw = xml_elt.attrib["CODE"]
        if len(cpv_code_raw) != 10:
            print("Length error for code (max 8+2):", cpv_code_raw)
        cpv["cpv_code"] = cpv_code_raw.split("-")[0]

        # name
        cpv_name_raw = xml_elt.find("TEXT/[@LANG='FR']").text
        if len(cpv_name_raw) > 255:
            print("Length error for name (max 255):", cpv_name_raw)
        cpv["name"] = cpv_name_raw[:255]

        cpv_list.append(cpv)

    print(f"Found {len(cpv_list)} items")
    return cpv_list


def cleanup_codes():
    print("-" * 80)
    print("Deleting existing Codes...")
    print(f"Found {Code.objects.count()} codes")
    print("Deleted!")
    Code.objects.all().delete()
    reset_app_sql_sequences("cpv")


class Command(BaseCommand):
    """
    How-to
    - download the XML file from https://simap.ted.europa.eu/fr/web/simap/cpv
    - run the script

    More info
    - if the code already exists, it will pass
    - 2008 CPV codes: 9454 in total

    Usage
    - poetry run python manage.py import_cpv
    """

    def handle(self, *args, **options):
        # Step 1: delete all existing codes
        # DANGER: some codes may have already been edited (Sector mapping)...
        # cleanup_codes()

        # Step 2: read the XML file
        cpv_list = read_xml()

        # Step 3: create the (new) Codes!
        print("-" * 80)
        print("Importing CPV Codes...")
        progress = 0
        for cpv in cpv_list:
            if Code.objects.filter(cpv_code=cpv["cpv_code"]).exists():
                print(f"{cpv['cpv_code']}: code already exists, skipping")
            else:
                progress += 1
                if (progress % 500) == 0:
                    print(f"{progress}...")
                Code.objects.create(**cpv)
