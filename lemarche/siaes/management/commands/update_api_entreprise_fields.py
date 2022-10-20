import time

from lemarche.siaes.models import Siae
from lemarche.utils.apis import api_slack
from lemarche.utils.apis.api_entreprise import siae_update_etablissement, siae_update_exercice
from lemarche.utils.commands import BaseCommand


class Command(BaseCommand):
    """
    Populates API Entreprise fields

    Note: Only on Siae who have api_entreprise_*_last_sync_date as None

    TODO: filter only on Siae not updated since a certain date?

    Usage: poetry run python manage.py update_api_entreprise_fields
    Usage: poetry run python manage.py update_api_entreprise_fields --scope etablissement
    Usage: poetry run python manage.py update_api_entreprise_fields --siret 01234567891011
    Usage: poetry run python manage.py update_api_entreprise_fields --limit 100
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--scope", type=str, default="all", help="Options are 'etablissement', 'exercice', or 'all'"
        )
        parser.add_argument("--siret", type=str, default=None, help="Lancer sur un Siret spécifique")
        parser.add_argument("--limit", type=int, default=None, help="Limiter le nombre de structures à processer")

    def handle(self, *args, **options):
        self.stdout_info("-" * 80)
        self.stdout_info("Populating API Entreprise fields...")

        if options["siret"]:
            siae_list = list(Siae.objects.filter(siret=options["siret"]))
        else:
            siae_list = list(
                Siae.objects.filter(api_entreprise_etablissement_last_sync_date=None)
                .filter(api_entreprise_exercice_last_sync_date=None)
                .order_by("id")
            )

        if options["limit"]:
            siae_list = siae_list[: options["limit"]]

        progress = 0
        success_count = {"etablissement": 0, "exercice": 0}

        self.stdout_info(f"Found {len(siae_list)} Siae")

        try:
            for siae in siae_list:
                progress += 1
                if (progress % 50) == 0:
                    self.stdout_info(f"{progress}...")
                # self.stdout_info("-" * 80)
                # self.stdout_info(f"{siae.id} / {siae.name} / {siae.siret}")
                if options["scope"] in ("all", "etablissement"):
                    result_etablissement = siae_update_etablissement(siae)
                    success_count["etablissement"] += result_etablissement
                if options["scope"] in ("all", "exercice"):
                    result_exercice = siae_update_exercice(siae)
                    success_count["exercice"] += result_exercice
                # small delay to avoid going above the API limitation
                # "max. 250 requêtes/min/jeton cumulées sur tous les endpoints"
                time.sleep(0.5)
            msg_success = [
                "----- Recap: sync API Entreprise -----",
                f"Done! Processed {len(siae_list)} siae",
                f"etablissements success count: {success_count['etablissement']}/{len(siae_list)}",
                f"exercices success count: {success_count['exercice']}/{len(siae_list)}",
            ]
            self.stdout_info(msg_success)
            api_slack.send_message_to_channel("\n".join(msg_success))
        except Exception as e:
            self.stdout_error(str(e))
            api_slack.send_message_to_channel("Erreur lors de la synchronisation API entreprises")
