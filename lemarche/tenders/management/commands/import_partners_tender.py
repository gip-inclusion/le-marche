import csv
import os

from django.core.management.base import BaseCommand

from lemarche.perimeters.models import Perimeter
from lemarche.tenders.models import PartnerShareTender


class Command(BaseCommand):
    """
    This script is used to import a list of partners from a csv
    To use it, get the csv list and call it list_partners_share_tenders.csv"

    Usage:
    python manage.py import_partners_tender
    python manage.py import_partners_tender --name test.csv
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--name",
            type=str,
            default="list_partners_share_tenders.csv",
            help="nom du fichier par défaut list_partners_share_tenders.csv",
        )

    def handle(self, *args, **options):
        self.stdout.write("-" * 80)
        self.stdout.write("Import des Partners...")
        self.stdout.write(f"Nombre de PartnerShareTender existants : {PartnerShareTender.objects.count()}")

        file_name = os.path.dirname(os.path.realpath(__file__)) + "/" + options["name"]

        with open(file_name) as csv_file:
            csvreader = csv.DictReader(csv_file, delimiter=",")
            for index, row in enumerate(csvreader):
                self.stdout.write("========")
                self.stdout.write(row["Nom de l'organisation"])
                self.stdout.write(row["Zone géographique"])
                partner = PartnerShareTender.objects.filter(name=row["Nom de l'organisation"])
                partner_exist = partner.count() > 0
                if partner_exist:
                    self.stdout.write("... existe déjà")
                    partner[0].contact_email_list.append(row["Email"])
                    partner[0].save()
                else:
                    partner = PartnerShareTender(name=row["Nom de l'organisation"], contact_email_list=[row["Email"]])
                    partner.save()
                    if row["Zone géographique"] and row["Zone géographique"] != "France entière":
                        perimeter = Perimeter.objects.get(name=row["Zone géographique"], kind=Perimeter.KIND_REGION)
                        partner.perimeters.add(perimeter)
                if ((index + 1) % 50) == 0:
                    self.stdout.write(f"{index + 1}...")

            self.stdout.write("========")
            self.stdout.write("Done")
            self.stdout.write(f"Nombre de PartnerShareTender : {PartnerShareTender.objects.count()}")
