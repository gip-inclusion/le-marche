import csv

from django import forms
from django.core.management.base import BaseCommand
from django.db.models import Case, EmailField, F, PositiveIntegerField, Value, When
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField

from lemarche.networks.models import Network
from lemarche.siaes.models import Siae


class HozmozImportForm(forms.ModelForm):
    YES_NO = (
        ("Oui", "Oui"),
        ("Non", "Non"),
    )
    is_in_network = forms.ChoiceField(choices=YES_NO, required=False)

    class Meta:
        model = Siae
        fields = [
            "contact_email",
            "contact_phone",
            "employees_insertion_count",
            "networks",
            "logo_url",
        ]

    def clean_is_in_network(self):
        data = self.cleaned_data["is_in_network"]
        if data == "Oui":
            return True
        elif data == "Non":
            return False
        raise forms.ValidationError("Valeur incorrecte")


class Command(BaseCommand):
    """
    Usage: poetry run python manage.py import_esat_gesat
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hosmoz_network = Network.objects.get(slug="hosmoz")

    def add_arguments(self, parser):
        parser.add_argument("--csv_file", dest="csv_file", required=True, type=str, help="Chemin du fichier CSV")

    def handle(self, *args, **options):
        csv_file = options["csv_file"]
        self.import_hosmoz(csv_file)

    def import_hosmoz(self, csv_file):
        with open(csv_file, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.import_row(row)

    def import_row(self, row):

        form_data = {
            "contact_email": row["Email"],
            "contact_phone": row["Tel public"],
            "employees_insertion_count": row["Nombre de travailleurs dans la structure (en ETP)"],
        }
        form = HozmozImportForm(form_data)
        if form.is_valid():
            self.stdout.write(self.style.SUCCESS(f"Row with SIRET {row['Siret']} ready to be updated !"))
        else:
            self.stdout.write(self.style.WARNING(f"Errors found with SIRET {row['Siret']} ready to be updated !"))
        cleaned_data = form.cleaned_data

        siret = row["Siret"].replace(" ", "")

        siaes = Siae.objects.filter(siret=siret)
        siaes.update(
            contact_email=Case(
                When(contact_email="", then=Value(cleaned_data.get("contact_email", ""))),
                default=F("contact_email"),
                output_field=EmailField(),
            ),
            contact_phone=Case(
                When(contact_phone="", then=Value(str(cleaned_data.get("contact_phone", "")))),
                default=F("contact_phone"),
                output_field=PhoneNumberField(),
            ),
            employees_insertion_count=Case(
                When(
                    employees_insertion_count__isnull=True,
                    then=Value(cleaned_data.get("employees_insertion_count", None)),
                ),
                default=F("employees_insertion_count"),
                output_field=PositiveIntegerField(),
            ),
            # If we update employees_insertion_count, then we also
            # need to update employees_insertion_count_last_updated date
            employees_insertion_count_last_updated=Case(
                When(employees_insertion_count__isnull=True, then=Value(timezone.now())),
                default=F("employees_insertion_count_last_updated"),
            ),
        )

        if cleaned_data.get("is_in_network"):
            siaes.get().networks.add(self.hosmoz_network)
