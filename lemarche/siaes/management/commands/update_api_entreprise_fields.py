import time

from django.core.management.base import BaseCommand

from lemarche.siaes.models import Siae
from lemarche.utils.apis.api_entreprise import siae_update_etablissement, siae_update_exercice


class Command(BaseCommand):
    """
    Usage: poetry run python manage.py update_api_entreprise_fields
    Usage: poetry run python manage.py update_api_entreprise_fields --scope etablissement
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--scope", type=str, default="all", help="Options are 'etablissement', 'exercice', or 'all'"
        )

    def handle(self, *args, **options):
        self.stdout.write("-" * 80)
        self.stdout.write("Populating API Entreprise fields...")

        siae_list = list(Siae.objects.all()[:100])

        success_count = {"etablissement": 0, "exercice": 0}

        for siae in siae_list:
            self.stdout.write("-" * 80)
            self.stdout.write(f"{siae.id} / {siae.name} / {siae.siret}")
            if options["scope"] in ("all", "etablissement"):
                result_etablissement = siae_update_etablissement(siae)
                success_count["etablissement"] += result_etablissement
            if options["scope"] in ("all", "exercice"):
                result_exercice = siae_update_exercice(siae)
                success_count["exercice"] += result_exercice
            # small delay to avoid going above the API limitation
            # "max. 250 requêtes/min/jeton cumulées sur tous les endpoints"
            time.sleep(0.5)

        self.stdout.write("-" * 80)
        self.stdout.write(f"Done! Processed {len(siae_list)} siae")
        self.stdout.write(f"/etablissements success count: {success_count['etablissement']}/{len(siae_list)}")
        self.stdout.write(f"/exercices success count: {success_count['exercice']}/{len(siae_list)}")
