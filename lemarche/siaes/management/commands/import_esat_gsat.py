import csv
import os
import re

from django.core.management.base import BaseCommand


FILE_PATH = os.path.dirname(os.path.realpath(__file__)) + "/" + "esat_gsat.csv"


class Command(BaseCommand):
    """ """

    def handle(self, *args, **options):
        self.read_csv()

    def read_csv(self):
        sector_list = list()
        # data_file = os.path.abspath(FILE_NAME)
        with open(FILE_PATH) as csv_file:
            csvreader = csv.DictReader(csv_file, delimiter=",")
            for index, row in enumerate(csvreader):
                print("==========")
                print(row)
                esat_sectors_string = row["Métiers"]
                esat_sectors_list = re.findall("[A-Z][^A-Z]*", esat_sectors_string)
                for esat_sector in esat_sectors_list:
                    if esat_sector.endswith(", "):
                        esat_sector = esat_sector[:-2]
                    sector_index = next(
                        (index for (index, s) in enumerate(sector_list) if (s["nom"] == esat_sector)), None
                    )
                    if sector_index is None:
                        sector_list.append({"nom": esat_sector, "count": 1})
                    else:
                        sector_list[sector_index]["count"] += 1

        for sector in sector_list:
            print(f"{sector['nom']};{sector['count']}")

    # def process_esat(esat):
