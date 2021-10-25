import os
from xml.etree import ElementTree

from django.core.management.base import BaseCommand

from lemarche.siaes.models import Siae


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
    # "type",
    # "secteurs",
]


def read_xml():
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
    """ """

    def handle(self, *args, **options):
        esat_list = read_xml()
        for esat in esat_list:
            self.process_esat(esat)

    def process_esat(self, esat):
        esat["kind"] = Siae.KIND_ESAT
        esat["source"] = Siae.SOURCE_ESAT
