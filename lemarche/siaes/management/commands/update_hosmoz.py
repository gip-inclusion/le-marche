import csv

from django import forms
from django.core.management.base import BaseCommand

from lemarche.siaes.models import Siae


class HozmozImportForm(forms.ModelForm):
    # contact_email = forms.EmailField(max_length=255, required=False)
    # contact_phone = PhoneNumberField(required=False)
    # employees_insertion_count = forms.IntegerField(required=False)

    class Meta:
        model = Siae
        fields = [
            "contact_email",
            "contact_phone",
            "employees_insertion_count",  # todo employees_insertion_count_last_updated
            "networks",
            "logo_url",
        ]


class Command(BaseCommand):
    """
    Usage: poetry run python manage.py import_esat_gesat
    """

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str, help="Chemin du fichier CSV")

    def handle(self, *args, **options):
        csv_file = options["csv_file"]
        self.import_hosmoz(csv_file)

    def import_hosmoz(self, csv_file):
        with open(csv_file, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.import_row(row)
                # print(row)
                # siae = Siae.objects.get(siret=row[0])
                # siae.is_in_hosmoz = row[1] == "OUI"
                # siae.save()

    @staticmethod
    def import_row(row):

        form_data = {
            "contact_email": row["Email"],
            "contact_phone": row["Tel public"],
            "employees_insertion_count": row["Nombre de travailleurs dans la structure (en ETP)"],
        }
        form = HozmozImportForm(form_data)
        if form.is_valid():
            print("VALID")
        else:
            print("INVALIDdddddddddddddd", form.errors)
        # Siae.objects.filter(siret=row["Siret"]).update(contact_email=row["HOSMOZ"] == "OUI")
