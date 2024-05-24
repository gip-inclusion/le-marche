from lemarche.sectors.models import Sector
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

    def handle(self, *args, **options):  # noqa C901
        added = 0
        delisted = 0
        email_updated = 0
        phone_updated = 0

        if options["csv_file"]:
            self.stdout_info("Importing SEP...")
            siae_list = read_sep_csv(options["csv_file"])
            group_by_city = {}  # group by city to handle multilines SEP, one line per sector
            for index, data in enumerate(siae_list):
                if data["Ville"] not in group_by_city:
                    group_by_city[data["Ville"]] = []

                group_by_city[data["Ville"]].append(data)

            for city, datas in group_by_city.items():
                try:
                    siae_same_city = Siae.objects.get(
                        siret=datas[0]["Siret"], city=datas[0]["Ville"], kind=siae_constants.KIND_SEP
                    )

                    if siae_same_city.user_count == 0:  # update only if siae has no user
                        # Update siae in db with the first line related to the same city
                        data = datas.pop(0)

                        sector = Sector.objects.get(name=data["Secteurs d'act list"][0])
                        if siae_same_city.sectors.count() > 1 or siae_same_city.sectors.first() != sector:
                            if options["dry_run"]:
                                self.stdout_info(f"sector needs to be erase per {sector}")
                            else:
                                self.stdout_success(f"sector has been erase per {sector}")
                                siae_same_city.sectors.set([sector])

                        if siae_same_city.address != data["Adresse"]:
                            self.stdout_error("Different address (but nothing will be done automatically): ")
                            self.stdout_error(f"Adresse csv {data['Adresse']} <-> {siae_same_city.address}")

                        email_updated += self.update_email_if_different(
                            siae_same_city, data["Email 1"], options["dry_run"]
                        )

                        phone_updated += self.update_phone(siae_same_city, data["Téléphone"], options["dry_run"])

                        # add other
                        for data in datas:
                            added += 1
                            if options["dry_run"]:
                                self.stdout_messages_success(["This SEP need to be add for its new sector :", data])
                            else:
                                self.import_sep(data, "sep")

                except Siae.DoesNotExist:
                    for data in datas:
                        added += 1
                        if options["dry_run"]:
                            self.stdout_messages_success(["This SEP need to be add :", data])
                        else:
                            self.import_sep(data, source="sep")
                except Siae.MultipleObjectsReturned:
                    self.stdout_error(f"Mutliple siae in db isn't yet supported (city : {city})")

        if options["csv_file_externe"]:
            self.stdout_info("Importing SEP Externe...")
            siae_list = read_sep_csv(options["csv_file_externe"])
            for index, data in enumerate(siae_list):
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

                        if siae_same_siret.user_count == 0:  # update only if siae has no user
                            email_updated += self.update_email_if_different(
                                siae_same_siret, data["Email 1"], options["dry_run"]
                            )
                            phone_updated += self.update_phone(siae_same_siret, data["Téléphone"], options["dry_run"])
                    except Siae.DoesNotExist:
                        added += 1
                        if options["dry_run"]:
                            self.stdout_messages_success(["This SEP externe need to be add :", data])
                        else:
                            self.import_sep(data, "sep_externe")

        self.stdout_success("Done !")
        if options["dry_run"]:
            self.stdout_messages_success(
                [
                    f"{added} new SEP needs to be added",
                    f"{delisted} old SEP needs to be delisted",
                    f"Email needs update : {email_updated}",
                    f"Phone needs update : {phone_updated}",
                ]
            )
        else:
            self.stdout_messages_success(
                [
                    f"{added} SIAE has been added",
                    f"{delisted} old SEP has been delisted",
                    f"{email_updated} email updated !",
                    f"{phone_updated} phone updated !",
                ]
            )

    def import_sep(self, data, source):
        sep_command = SepCommand()

        [data.pop(key) for key in USELESS_COLUMN_NAME_LIST if key in data]
        sep_command.import_sep(data, source=source)
        self.stdout_messages_success(["This SEP has been added :", data])

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

    def update_phone(self, siae, phone, dry_run):
        phone_before = siae.contact_phone
        phone = phone.replace(" ", "")
        if dry_run:
            self.stdout_info(f"Contact phone need update : {phone_before} <- {phone}")
        else:
            siae.contact_phone = phone
            siae.save()
            self.stdout_success(f"Phone updated :{phone_before} <- {phone}")
        return 1
