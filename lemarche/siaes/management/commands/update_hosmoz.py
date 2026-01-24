import csv

import boto3
from django import forms
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Case, EmailField, F, PositiveIntegerField, URLField, Value, When
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField

from config.settings.base import SIAE_CLIENT_REFERENCE_LOGO_FOLDER_NAME
from lemarche.networks.models import Network
from lemarche.siaes.models import Siae
from lemarche.utils.s3 import API_CONNECTION_DICT


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
    csv_file: path to the csv file
    logo_folder: path to the folder containing the logos in *.png format
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hosmoz_network = Network.objects.get(slug="hosmoz")
        # init S3 config
        self.bucket_name = settings.S3_STORAGE_BUCKET_NAME
        resource = boto3.resource("s3", **API_CONNECTION_DICT)
        self.bucket = resource.Bucket(self.bucket_name)

    def add_arguments(self, parser):
        parser.add_argument("--csv_file", dest="csv_file", required=True, type=str, help="Chemin du fichier CSV")
        parser.add_argument(
            "--logo-folder", dest="logo_folder", required=True, type=str, help="Chemin du dossier des logos"
        )
        parser.add_argument(
            "--dry-run",
            dest="dry_run",
            required=False,
            type=bool,
            default=True,
            help="Dry run (pas de changement en base. Default: True)",
        )

    def handle(self, *args, **options):
        self.csv_file = options["csv_file"]
        self.logo_folder = options["logo_folder"]
        self.dry_run = options["dry_run"]

        self.import_hosmoz()

    def import_hosmoz(self):
        with open(self.csv_file) as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.import_row(row)

    def get_logo_url(self, logo_id: str) -> str:
        """From a logo_id, returns the url of the logo on S3 after uploading it"""
        logo_file_path = f"{self.logo_folder}/{logo_id}.png"
        bucket_path = f"{SIAE_CLIENT_REFERENCE_LOGO_FOLDER_NAME}/hosmoz/{logo_id}.png"
        try:
            self.bucket.upload_file(
                logo_file_path,
                bucket_path,
                ExtraArgs={"ACL": "public-read", "ContentType": "image/png"},
            )
        except FileNotFoundError:
            self.stdout.write(self.style.WARNING(f"Logo {logo_id} not found !"))
            return ""
        else:
            return f"{API_CONNECTION_DICT['endpoint_url']}/{self.bucket_name}/{bucket_path}"

    def import_row(self, row):
        form_data = {
            "contact_email": row["Email"],
            "contact_phone": row["Tel public"],
            "employees_insertion_count": row["Nombre de travailleurs dans la structure (en ETP)"],
            "is_in_network": row["Adhérent Hosmoz"],
        }
        form = HozmozImportForm(form_data)
        if form.is_valid():
            self.stdout.write(self.style.SUCCESS(f"Row with SIRET {row['Siret']} ready to be updated !"))
        else:
            self.stdout.write(self.style.WARNING(f"Errors found with SIRET {row['Siret']} ready to be updated !"))
        cleaned_data = form.cleaned_data

        siret = row["Siret"].replace(" ", "")

        siaes = Siae.objects.filter(siret=siret)

        if self.dry_run:
            self.stdout.write(self.style.WARNING(f"Not saving {row['Siret']} because it is a dry run !"))
            return

        s3_logo_url = self.get_logo_url(row["Id"])

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
            logo_url=Case(
                When(logo_url="", then=Value(s3_logo_url)),
                default=F("logo_url"),
                output_field=URLField(),
            ),
        )

        if cleaned_data.get("is_in_network"):
            siaes.get().networks.add(self.hosmoz_network)
