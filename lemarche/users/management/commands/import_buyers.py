import csv

from django.core.management.base import BaseCommand

from lemarche.users.models import User


class Command(BaseCommand):
    """Import new buyers from a csv file."""

    def add_arguments(self, parser):
        parser.add_argument(
            "filename",
            type=str,
            help="Fichier csv contenant les acheteurs à importer.",
        )
        parser.add_argument(
            "--brevo-template_id",
            type=int,
            help="ID de la template de mail Brevo pour envoyer l'invitation aux acheteurs importés.",
        )
        parser.add_argument(
            "--brevo-contact_id",
            type=int,
            help="ID de la liste de contact Brevo à utiliser pour les acheteurs importés.",
        )

    def handle(self, *args, **options):
        with open(options["filename"], "r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            imported_list = list(reader)

        for imported_user in imported_list:
            User.objects.create_user(
                email=imported_user["EMAIL"],
                first_name=imported_user["FIRST_NAME"],
                last_name=imported_user["LAST_NAME"],
                phone=imported_user["PHONE"],
                kind=User.KIND_BUYER,
                # company_name=imported_user["Nom de la société"],
                position=imported_user["POSITION"],
                accept_rgpd=True,
                accept_survey=True,
                password=None,
            )
