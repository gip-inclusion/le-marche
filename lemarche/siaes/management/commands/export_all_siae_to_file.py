import csv
from datetime import date

from django.core.management.base import BaseCommand

from lemarche.utils.export import export_siae_to_csv, export_siae_to_excel
from lemarche.www.siaes.forms import SiaeSearchForm


class Command(BaseCommand):
    """
    Export all Siae to a file (XLS or CSV)

    Usage:
    poetry run python manage.py export_all_siae_to_file
    poetry run python manage.py export_all_siae_to_file  --format csv
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--format", type=str, choices=["xls", "csv"], default="xls", help="Options are 'xls' (default) or 'csv'"
        )

    def handle(self, *args, **options):
        filename = f"liste_structures_{date.today()}"

        filter_form = SiaeSearchForm({})
        siae_list = filter_form.filter_queryset()

        if options["format"] == "csv":
            file = open(f"{filename}.csv", "w")
            writer = csv.writer(file)
            export_siae_to_csv(writer, siae_list)
            file.close()

        else:  # xls
            wb = export_siae_to_excel(siae_list)
            wb.save(f"{filename}.xls")
