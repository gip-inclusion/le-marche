import csv
import os
import re

from django.core.management.base import BaseCommand


FILE_NAME = "esat_gsat_2.csv"
FILE_PATH = os.path.dirname(os.path.realpath(__file__)) + "/" + FILE_NAME


def read_csv():
    esat_list = list()
    sector_list = list()

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
                sector_index = next(
                    (index for (index, s) in enumerate(sector_list) if (s["nom"] == esat_sector)), None
                )
                if sector_index is None:
                    sector_list.append({"nom": esat_sector, "count": 1})
                else:
                    sector_list[sector_index]["count"] += 1

            esat_list.append(row)

    return esat_list


class Command(BaseCommand):
    """ """

    def handle(self, *args, **options):
        esat_list = read_csv()
        print(len(esat_list))

    # def process_esat(esat):
