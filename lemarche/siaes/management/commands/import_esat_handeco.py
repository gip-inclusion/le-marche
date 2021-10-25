import os
from xml.etree import ElementTree

from django.core.management.base import BaseCommand


FILE_PATH = os.path.dirname(os.path.realpath(__file__)) + "/" + "esat_handeco.xml"


class Command(BaseCommand):
    """ """

    def handle(self, *args, **options):
        self.read_xml()

    def read_xml(self):
        sector_list = list()
        # data_file = os.path.abspath(FILE_NAME)
        data_file = os.path.abspath(FILE_PATH)
        xml_tree = ElementTree.parse(data_file)
        xml_root = xml_tree.getroot()
        for xml_elt in xml_root.findall("structure"):
            print("==========")
            print(xml_elt)
            esat_sectors = xml_elt.find("secteurs")
            for esat_sector in esat_sectors.findall("secteur"):
                sector_nom = esat_sector.find("secteurnom").text
                sector_activite = esat_sector.find("activite").text
                print(sector_nom, sector_activite)
                print(len(sector_list))
                sector_index = next(
                    (
                        index
                        for (index, s) in enumerate(sector_list)
                        if ((s["nom"] == sector_nom) and (s["activite"] == sector_activite))
                    ),
                    None,
                )
                if sector_index is None:
                    sector_list.append({"nom": sector_nom, "activite": sector_activite, "count": 1})
                else:
                    sector_list[sector_index]["count"] += 1

        for sector in sector_list:
            print(f"{sector['nom']};{sector['activite']};{sector['count']}")

    # def process_esat(esat):
