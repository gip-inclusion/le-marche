import csv
import os

from django.utils import timezone

from lemarche.siaes import constants as siae_constants
from lemarche.siaes.models import Siae
from lemarche.utils.apis.geocoding import get_geocoding_data
from lemarche.utils.commands import BaseCommand
from lemarche.utils.constants import DEPARTMENT_TO_REGION, department_from_postcode


class Command(BaseCommand):
    help = "Import esat data from a CSV file with the Siae model"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Dry run (no changes to the DB)")
        parser.add_argument("csv_file", type=str, help="Path to the CSV file containing esat data")

    def handle(self, *args, **options):  # noqa C901
        file_path = options["csv_file"]

        already_exists = 0
        new = 0
        news = ""
        multiple_for_siret = 0
        email_updated = 0
        phone_updated = 0
        employees_count_updated = 0

        with open(file_path, encoding="utf-8") as file:
            reader = csv.DictReader(file, delimiter="|")
            for data in reader:
                # csv header: "Raison sociale"|"Siret"|"Type de structure"|"Métiers proposés"|"Adresse"|"Code Postal|"
                #             "Ville"|"Téléphone"|"Adresse e-mail"|"Nombre de travailleurs dans la structure (en ETP)"
                siret = data["Siret"].replace(" ", "")
                name = data["Raison sociale"]
                kind = data["Type de structure"]
                phone = data["Téléphone"].replace(" ", "")
                email = data["Adresse e-mail"].lower()
                employees_count = data["Nombre de travailleurs dans la structure (en ETP)"]

                if kind == siae_constants.KIND_ESAT:  # import only ESAT
                    try:
                        siae = Siae.objects.get(siret=siret)
                        self.stdout_info(f"{name} already exists (SIRET: {siret}).")
                        already_exists += 1

                        contact_email_before = siae.contact_email
                        if siae.user_count == 0:  # update only if siae has no user
                            if email and email != contact_email_before:
                                email_updated += 1
                                if options["dry_run"]:
                                    self.stdout_info(f"Email need update :{contact_email_before} <- {email}")
                                else:
                                    siae.contact_email = email
                                    siae.save()
                                    self.stdout_success(f"Email updated :{contact_email_before} <- {email}")

                            contact_phone_before = siae.contact_phone
                            if phone:
                                phone_updated += 1
                                if options["dry_run"]:
                                    self.stdout_info(f"Phone need update :{contact_phone_before} <- {phone}")
                                else:
                                    siae.contact_phone = phone
                                    siae.save()
                                    self.stdout_success(f"Phone updated :{contact_phone_before} <- {phone}")

                        employees_insertion_count_before = siae.employees_insertion_count
                        if employees_count != "#N/D" and int(employees_count) != employees_insertion_count_before:
                            employees_count_updated += 1
                            if options["dry_run"]:
                                self.stdout_info(
                                    f"Employees insertion count need update :"
                                    f"{employees_insertion_count_before} <- {employees_count}"
                                )
                            else:
                                siae.employees_insertion_count = int(employees_count)
                                siae.employees_insertion_count_last_updated = timezone.now()
                                siae.save()
                                self.stdout_success(
                                    f"Employees insertion count updated :"
                                    f"{employees_insertion_count_before} <- {employees_count}"
                                )

                    except Siae.MultipleObjectsReturned:
                        already_exists += 1
                        multiple_for_siret += 1
                        self.stdout_warning(f"Multiple company with SIRET: {siret}")
                    except Siae.DoesNotExist:
                        new += 1
                        news += f"SIRET: {siret} NAME: {name}\n"

                        if options["dry_run"]:
                            self.stdout_success(f"Company {name} ({siret}) needs to be added ")
                        else:
                            data["import_source"] = os.path.basename(file.name)

                            new_siae_fields = {
                                "name": name,
                                "siret": siret,
                                "contact_email": email,
                                "contact_phone": phone,
                                "employees_insertion_count": (
                                    int(employees_count) if employees_count and employees_count != "#N/D" else None
                                ),
                                "employees_insertion_count_last_updated": timezone.now(),
                                "import_raw_object": data.copy(),
                                "kind": siae_constants.KIND_ESAT,
                                "source": siae_constants.SOURCE_ESAT,
                                "geo_range": siae_constants.GEO_RANGE_DEPARTMENT,
                            }
                            new_siae = Siae.objects.create(**new_siae_fields)

                            full_address = f"{data['Adresse']} {data['Code Postal']} {data['Ville']}"
                            geocoding_data = get_geocoding_data(full_address)
                            if geocoding_data:
                                print(geocoding_data)
                                new_siae.address = geocoding_data["address"]
                                new_siae.post_code = geocoding_data["post_code"]
                                new_siae.city = geocoding_data["city"]
                                new_siae.department = department_from_postcode(geocoding_data["post_code"])
                                new_siae.region = DEPARTMENT_TO_REGION[siae.department]
                                new_siae.coords = geocoding_data["coords"]
                                new_siae.save()

                            self.stdout_success(f"Company {name} ({siret}) has been added ")

        self.stdout_info("-" * 80)
        self.stdout_info(f"already_exists : {already_exists}")
        self.stdout_warning(f"multiple_for_siret : {multiple_for_siret}")

        if options["dry_run"]:
            self.stdout_messages_success(
                [
                    f"Email needs update : {email_updated}",
                    f"Phone needs update : {phone_updated}",
                    f"Employees count needs update : {employees_count_updated}",
                    f"{new} new siaes needs to be added : ",
                    news,
                ]
            )
        else:
            self.stdout_messages_success(
                [
                    f"{email_updated} email updated !",
                    f"{phone_updated} phone updated !",
                    f"{employees_count_updated} employees count updated !",
                    f"{new} new siaes has been added : ",
                    news,
                ]
            )

        self.stdout_info("-" * 80)
