import openpyxl
from django.core.management.base import BaseCommand

from lemarche.siaes.models import SiaeESUS


class Command(BaseCommand):
    help = "Import data into SiaeESUS from ESUS xlsx sheet"

    def add_arguments(self, parser):
        parser.add_argument("--xlsx-file", dest="xlsx_file", required=True, help="File from ESUS listing")

    def handle(self, *args, **options):
        xlsx_file = options["xlsx_file"]

        with open(xlsx_file, "rb") as file_content:
            workbook = openpyxl.load_workbook(file_content)
            sheet = workbook.active

            # For some reason, the first row is empty
            assert sheet["B1"].value == "SIREN"

            bulk_model_list = []
            for row in sheet.iter_rows(min_row=2):
                # B column contains Siren
                siren = str(row[1].value)

                if not len(siren) == 9:
                    self.stdout.write(self.style.ERROR(f"Skipping {siren} because it is not a valid Siren"))
                    continue

                siae_esus = SiaeESUS(siren=siren)

                bulk_model_list.append(siae_esus)

            SiaeESUS.objects.bulk_create(bulk_model_list, ignore_conflicts=True)
