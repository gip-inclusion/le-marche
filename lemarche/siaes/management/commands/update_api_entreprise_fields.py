import time

from django.db.models import Q

from lemarche.siaes.models import Siae
from lemarche.utils.apis import api_slack
from lemarche.utils.apis.api_entreprise import siae_update_etablissement, siae_update_exercice
from lemarche.utils.commands import BaseCommand


SCOPE_ALLOWED_VALUES = ("all", "etablissement", "exercice")


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

        if options["scope"] not in SCOPE_ALLOWED_VALUES:
            raise Exception(f"scope not in {SCOPE_ALLOWED_VALUES}")

        if options["siret"]:
            siae_queryset = Siae.objects.filter(siret=options["siret"])
        else:
            siae_queryset = Siae.objects.filter(
                Q(api_entreprise_etablissement_last_sync_date=None) | Q(api_entreprise_exercice_last_sync_date=None)
            ).order_by("id")

        if options["limit"]:
            siae_queryset = siae_queryset[: options["limit"]]

        # self.stdout_info(f"Found {siae_queryset.count()} Siae")

        # API Entreprise : etablissements
        if options["scope"] in ("all", "etablissement"):
            progress = 0
            results = {"success": 0, "error": 0}
            siae_queryset_etablissement = siae_queryset.filter(api_entreprise_etablissement_last_sync_date=None)
            self.stdout_info("-" * 80)
            self.stdout_info(f"Populating 'etablissement' for {siae_queryset_etablissement.count()} Siae...")

            for siae in siae_queryset_etablissement:
                try:
                    progress += 1
                    if (progress % 50) == 0:
                        self.stdout_info(f"{progress}...")
                    # self.stdout_info("-" * 80)
                    # self.stdout_info(f"{siae.id} / {siae.name} / {siae.siret}")
                    response, message = siae_update_etablissement(siae)
                    if response:
                        results["success"] += 1
                    else:
                        self.stdout_error(str(message))
                        results["error"] += 1
                    # small delay to avoid going above the API limitation
                    # "max. 250 requêtes/min/jeton cumulées sur tous les endpoints"
                    time.sleep(0.5)
                except Exception as e:
                    self.stdout_error(str(e))
                    api_slack.send_message_to_channel(
                        "Erreur lors de la synchronisation API entreprises : etablissements"
                    )

            msg_success = [
                "----- Recap: sync API Entreprise : etablissements -----",
                f"Done! Processed {siae_queryset_etablissement.count()} siae",
                f"success count: {results['success']}/{siae_queryset_etablissement.count()}",
                f"error count: {results['error']}/{siae_queryset_etablissement.count()} (voir les logs)",
            ]
            self.stdout_messages_success(msg_success)
            api_slack.send_message_to_channel("\n".join(msg_success))

        # API Entreprise : exercices
        if options["scope"] in ("all", "exercice"):
            progress = 0
            results = {"success": 0, "error": 0}
            siae_queryset_exercice = siae_queryset.filter(api_entreprise_exercice_last_sync_date=None)
            self.stdout_info("-" * 80)
            self.stdout_info(f"Populating 'exercice' for {siae_queryset_exercice.count()} Siae...")

            for siae in siae_queryset_exercice:
                try:
                    progress += 1
                    if (progress % 50) == 0:
                        self.stdout_info(f"{progress}...")
                    # self.stdout_info("-" * 80)
                    # self.stdout_info(f"{siae.id} / {siae.name} / {siae.siret}")
                    response, message = siae_update_exercice(siae)
                    if response:
                        results["success"] += 1
                    else:
                        self.stdout_error(str(message))
                        results["error"] += 1
                    # small delay to avoid going above the API limitation
                    # "max. 250 requêtes/min/jeton cumulées sur tous les endpoints"
                    time.sleep(0.5)
                except Exception as e:
                    self.stdout_error(str(e))
                    api_slack.send_message_to_channel("Erreur lors de la synchronisation API entreprises : exercices")

            msg_success = [
                "----- Recap: sync API Entreprise : exercices -----",
                f"Done! Processed {siae_queryset_exercice.count()} siae",
                f"success count: {results['success']}/{siae_queryset_exercice.count()}",
                f"error count: {results['error']}/{siae_queryset_exercice.count()} (voir les logs)",
            ]
            self.stdout_messages_success(msg_success)
            api_slack.send_message_to_channel("\n".join(msg_success))
