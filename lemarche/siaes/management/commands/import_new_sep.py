from lemarche.siaes import constants as siae_constants
from lemarche.siaes.management.commands.import_sep import Command as SepCommand, read_csv as read_sep_csv
from lemarche.siaes.models import Siae
from lemarche.utils.commands import BaseCommand


USELESS_COLUMN_NAME_LIST = [
    "Type de prestation",
    "Secteurs d'act 4",
    "Secteurs d'act 5",
    "Secteurs d'act 6",
    "Secteurs d'act 7",
    "Secteurs d'act 8",
    "Secteurs d'act 9",
]


class Command(BaseCommand):
    help = "Import new SEP and delisted old"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Dry run (no changes to the DB)")
        parser.add_argument(
            "--csv-file", dest="csv_file", type=str, help="Path to the CSV file containing SEP data", default=""
        )
        parser.add_argument(
            "--csv-file-externe",
            dest="csv_file_externe",
            type=str,
            help="Path to the CSV file containing externe SEP data",
            default="",
        )

    def handle(self, *args, **options):
        sep_command = SepCommand()

        added = 0
        delisted = 0
        email_updated = 0
        phone_updated = 0

        if options["csv_file"]:
            self.stdout_info("Importing SEP...")
            siae_list = read_sep_csv(options["csv_file"])
            progress = 0
            for index, data in enumerate(siae_list):
                progress += 1
                if (progress % 10) == 0:
                    self.stdout_info(f"{progress}...")

                try:
                    # TODO: fix email and phone update when there are several lines for the same SEP
                    siae_same_city = Siae.objects.get(
                        siret=data["Siret"], city=data["Ville"], kind=siae_constants.KIND_SEP
                    )

                    if siae_same_city.address != data["Adresse"]:
                        self.stdout_error("Different address (but nothing will be done automatically): ")
                        self.stdout_error(f"Adresse csv {data['Adresse']} <-> {siae_same_city.address}")

                    email_updated += self.update_email_if_different(
                        siae_same_city, data["Email 1"], options["dry_run"]
                    )

                    phone_updated += self.update_phone_if_different(
                        siae_same_city, data["Téléphone"], options["dry_run"]
                    )

                except Siae.DoesNotExist:
                    added += 1
                    if options["dry_run"]:
                        self.stdout_success("This SEP need to be add :")
                        self.stdout_success(data)
                    else:
                        [data.pop(key) for key in USELESS_COLUMN_NAME_LIST if key in data]
                        sep_command.import_sep(data, source="sep")
                        self.stdout_success("This SEP has been added :")
                        self.stdout_success(data)

        if options["csv_file_externe"]:
            self.stdout_info("Importing SEP Externe...")
            siae_list = read_sep_csv(options["csv_file_externe"])
            progress = 0
            for index, data in enumerate(siae_list):
                progress += 1
                if (progress % 10) == 0:
                    self.stdout_info(f"{progress}...")

                if data["A Supprimer"] == "1":
                    siae_with_siret = Siae.objects.get(siret=data["Siret"], kind=siae_constants.KIND_SEP)
                    if not siae_with_siret.is_delisted:
                        delisted += 1
                        if options["dry_run"]:
                            self.stdout_error("Siae need to be delisted")
                            self.stdout_error(data)
                        else:
                            siae_with_siret.is_delisted = True
                            siae_with_siret.save()
                            self.stdout_success("Siae {siae_with_siret} has beed delisted !")

                else:
                    # useless column afterwards
                    data.pop("A Supprimer")

                    try:
                        siae_same_siret = Siae.objects.get(siret=data["Siret"], kind=siae_constants.KIND_SEP)
                        if siae_same_siret.city != data["Ville"] or siae_same_siret.address != data["Adresse"]:
                            self.stdout_error("Different address (but nothing will be done automatically): ")
                            self.stdout_error(f"Ville csv {data['Ville']} <->  {siae_same_siret.city}")
                            self.stdout_error(f"Adresse csv {data['Adresse']} <-> {siae_same_siret.address}")

                        email_updated += self.update_email_if_different(
                            siae_same_siret, data["Email 1"], options["dry_run"]
                        )
                        phone_updated += self.update_phone_if_different(
                            siae_same_siret, data["Téléphone"], options["dry_run"]
                        )
                    except Siae.DoesNotExist:
                        added += 1
                        if options["dry_run"]:
                            self.stdout_success("This SEP externe need to be add :")
                            self.stdout_success(data)
                        else:
                            [data.pop(key) for key in USELESS_COLUMN_NAME_LIST if key in data]
                            sep_command.import_sep(data, source="sep_externe")
                            self.stdout_success("This SEP externe has been added :")
                            self.stdout_success(data)

        self.stdout_success("Done !")
        if options["dry_run"]:
            self.stdout_success(f"{added} new SEP needs to be added")
            self.stdout_success(f"{delisted} old SEP needs to be delisted")
            self.stdout_success(f"Email needs update : {email_updated}")
            self.stdout_success(f"Phone needs update : {phone_updated}")
        else:
            self.stdout_success(f"{added} SIAE has been added")
            self.stdout_success(f"{delisted} old SEP has been delisted")
            self.stdout_success(f"{email_updated} email updated !")
            self.stdout_success(f"{phone_updated} phone updated !")

    def update_email_if_different(self, siae, email, dry_run):
        contact_email_before = siae.contact_email
        if contact_email_before != email:
            if dry_run:
                self.stdout_info(f"Contact email need update :  {contact_email_before} <- {email}")
            else:
                siae.contact_email = email
                siae.save()
                self.stdout_success(f"Email updated :{contact_email_before} <- {email}")
            return 1
        return 0

    def update_phone_if_different(self, siae, phone, dry_run):
        phone_before = siae.contact_phone.replace(" ", "")
        phone = phone.replace(" ", "")
        if phone_before != phone:
            if dry_run:
                self.stdout_info(f"Contact phone need update : {phone_before} <- {phone}")
            else:
                siae.contact_phone = phone
                siae.save()
                self.stdout_success(f"Phone updated :{phone_before} <- {phone}")
            return 1
        return 0
